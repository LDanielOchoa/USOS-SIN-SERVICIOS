from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from celery import Celery
from time import sleep

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['CELERY_BROKER_URL'] = os.getenv('redis://default:HsqFHMNwOUoyKxgZJinISnFIeBZozxfA@redis.railway.internal:6379')  # Usar variable de entorno
app.config['CELERY_RESULT_BACKEND'] = os.getenv('redis://default:HsqFHMNwOUoyKxgZJinISnFIeBZozxfA@redis.railway.internal:6379')  # Usar variable de entorno


celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

def custom_date_parser(date_str):
    try:
        return pd.to_datetime(date_str, format='%d/%m/%Y %H:%M:%S')
    except ValueError:
        try:
            return pd.to_datetime(date_str, format='%d/%m/%Y %H:%M')
        except ValueError:
            try:
                date_str_fixed = date_str.replace(' 24:', '00:', 1)
                return pd.to_datetime(date_str_fixed, format='%d/%m/%Y %H:%M')
            except ValueError:
                return None

@celery.task(bind=True)
def process_files(self, servicios_path, usos_path):
    try:
        # Fase 1: Cargando archivos
        self.update_state(state='PROGRESS', meta={'current': 25, 'status': 'Cargando archivos...'})
        sleep(2)  # Simulamos una pausa para mostrar el progreso
        tabla1 = pd.read_excel(servicios_path, parse_dates=['Inicio de Servicio', 'Fin de Servicio'], date_parser=custom_date_parser)
        tabla2 = pd.read_excel(usos_path, parse_dates=['Fecha Uso'], date_parser=custom_date_parser)

        # Fase 2: Procesando datos
        self.update_state(state='PROGRESS', meta={'current': 50, 'status': 'Procesando datos...'})
        sleep(2)
        tabla1['Inicio de Servicio'] = pd.to_datetime(tabla1['Inicio de Servicio'])
        tabla1['Fin de Servicio'] = pd.to_datetime(tabla1['Fin de Servicio'])
        tabla2['Fecha Uso'] = pd.to_datetime(tabla2['Fecha Uso'])

        tabla1['Inicio de Servicio'] = tabla1['Inicio de Servicio'].dt.floor('T')
        tabla1['Fin de Servicio'] = tabla1['Fin de Servicio'].dt.floor('T')
        tabla2['Fecha Uso'] = tabla2['Fecha Uso'].dt.floor('T')

        tabla1['Vehículos'] = tabla1['Vehículos'].str.replace('SAO-', '', regex=False)
        tabla2['Equipo'] = tabla2['Equipo'].str.replace('SAO', '', regex=False)

        tabla1.sort_values(by=['Vehículos', 'Inicio de Servicio'], inplace=True)

        usuarios_sin_servicio = []
        for index, uso in tabla2.iterrows():
            fecha_uso = uso['Fecha Uso']
            codigo_equipo = uso['Equipo']

            servicio = tabla1[(tabla1['Vehículos'] == codigo_equipo) & 
                              (tabla1['Inicio de Servicio'] <= fecha_uso) & 
                              (tabla1['Fin de Servicio'] >= fecha_uso)]

            if servicio.empty:
                usuarios_sin_servicio.append(uso)

        usuarios_sin_servicio_df = pd.DataFrame(usuarios_sin_servicio)

        # Fase 3: Guardando archivo
        self.update_state(state='PROGRESS', meta={'current': 75, 'status': 'Generando archivo...'})
        sleep(2)
        output_path = os.path.join('temp', 'usos_sin_servicios_septiembre.xlsx')
        usuarios_sin_servicio_df.to_excel(output_path, index=False)

        # Limpiar archivos temporales (opcional)
        os.remove(servicios_path)
        os.remove(usos_path)

        # Fase 4: Completado, archivo disponible para descarga
        self.update_state(state='PROGRESS', meta={'current': 100, 'status': 'Proceso completado. Archivo listo para descargar.'})
        return {'current': 100, 'status': 'Completado', 'result': output_path}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise

@app.route('/upload', methods=['POST'])
def upload_files():
    servicios_file = request.files['servicios']
    usos_file = request.files['usos']

    os.makedirs('temp', exist_ok=True)
    servicios_path = os.path.join('temp', servicios_file.filename)
    usos_path = os.path.join('temp', usos_file.filename)
    servicios_file.save(servicios_path)
    usos_file.save(usos_path)

    task = process_files.apply_async(args=[servicios_path, usos_path])

    return jsonify({'message': 'Proceso iniciado', 'task_id': task.id})

@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = process_files.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'current': 0, 'status': 'Pendiente...'}
    elif task.state == 'PROGRESS':
        response = {'state': task.state, 'current': task.info.get('current', 0), 'status': task.info.get('status', '')}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'current': 100, 'status': 'Completado', 'result': task.result.get('result')}
    else:
        response = {'state': task.state, 'status': str(task.info)}
    return jsonify(response)

@app.route('/download/<task_id>', methods=['GET'])
def download_file(task_id):
    task = process_files.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        output_path = task.result['result']
        return send_file(output_path, as_attachment=True)
    else:
        return jsonify({'error': 'Archivo no disponible o el proceso no ha finalizado.'}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
