<template>
  <div class="container mx-auto mt-10 p-8 max-w-lg shadow-lg rounded-xl bg-gray-400">
    <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">Subir Archivos</h2>

    <!-- Input para informe de servicios -->
    <div class="mb-6">
      <label class="block text-gray-600 font-medium mb-2">Informe de Servicios</label>
      <input type="file" @change="handleFileChange('servicios', $event)" class="file-input" />
    </div>

    <!-- Input para informe de usos -->
    <div class="mb-6">
      <label class="block text-gray-600 font-medium mb-2">Informe de Usos</label>
      <input type="file" @change="handleFileChange('usos', $event)" class="file-input" />
    </div>

    <!-- Botón de carga -->
    <button 
      @click="uploadFiles" 
      :disabled="isUploading" 
      class="upload-btn"
    >
      <span v-if="isUploading">Cargando...</span>
      <span v-else>Cargar Archivos</span>
    </button>

    <!-- Barra de progreso -->
    <div v-if="taskStatus && !isCompleted" class="mt-6">
      <p class="text-gray-700 mb-2">Progreso:</p>
      <div class="relative h-4 bg-gray-300 rounded-full overflow-hidden">
        <div class="bg-gradient-to-r from-green-400 to-blue-500 h-full" :style="{ width: progress + '%' }"></div>
      </div>
      <p class="mt-2 text-sm text-gray-600">{{ progressMessage }}</p>
    </div>

    <!-- Mensaje de éxito o error -->
    <div v-if="isCompleted" class="mt-6 text-center">
      <p v-if="taskStatus === 'SUCCESS'" class="text-lg font-semibold text-green-600">¡Archivos procesados con éxito!</p>
      <p v-else-if="taskStatus === 'FAILURE'" class="text-lg font-semibold text-red-600">Error al procesar los archivos.</p>
      <button v-if="taskStatus === 'SUCCESS'" @click="downloadFile" class="mt-4 download-btn">
        Descargar Archivo
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      files: {
        servicios: null,
        usos: null,
      },
      taskId: null,
      taskStatus: '',
      progress: 0, // Estado de la barra de progreso
      isUploading: false,
      isCompleted: false,
      downloadLink: '', // Enlace para descargar el archivo
    };
  },
  computed: {
    progressMessage() {
      if (this.progress < 100) {
        return `Procesando (${this.progress}%)...`;
      } else if (this.taskStatus === 'SUCCESS') {
        return '¡Completado!';
      } else if (this.taskStatus === 'FAILURE') {
        return 'Error en el procesamiento';
      }
    },
  },
  methods: {
    handleFileChange(type, event) {
      this.files[type] = event.target.files[0];
    },
    async uploadFiles() {
      this.isUploading = true;
      this.isCompleted = false;
      this.progress = 0;

      const formData = new FormData();
      formData.append('servicios', this.files.servicios);
      formData.append('usos', this.files.usos);

      try {
        const response = await axios.post('http://sao66.up.railway.app/upload', formData);
        this.taskId = response.data.task_id;
        this.taskStatus = 'PROGRESS'; // Cambiamos el estado a PROGRESS

        // Iniciar la verificación de estado de la tarea
        this.checkTaskProgress();
      } catch (error) {
        console.error('Error al cargar archivos:', error);
        this.taskStatus = 'FAILURE';
        this.isUploading = false;
      }
    },
    async checkTaskProgress() {
      if (!this.taskId) return;

      const intervalId = setInterval(async () => {
        try {
          const response = await axios.get(`http://localhost:5000/status/${this.taskId}`);
          this.taskStatus = response.data.state;

          // Actualiza la barra de progreso
          if (this.taskStatus === 'PENDING') {
            this.progress = 25;
          } else if (this.taskStatus === 'STARTED') {
            this.progress = 50;
          } else if (this.taskStatus === 'SUCCESS') {
            this.progress = 100;
            this.isCompleted = true;
            clearInterval(intervalId); // Detén la verificación cuando termine
            this.downloadLink = response.data.result; // Obtener el enlace para descargar el archivo
          } else if (this.taskStatus === 'FAILURE') {
            this.isCompleted = true;
            clearInterval(intervalId);
          }
        } catch (error) {
          console.error('Error al consultar el estado de la tarea:', error);
          this.taskStatus = 'FAILURE';
          clearInterval(intervalId);
        }
      }, 2000); // Consulta el estado cada 2 segundos
    },
    downloadFile() {
      if (this.downloadLink) {
        // Abre el enlace en una nueva pestaña para descargar
        window.open(this.downloadLink, '_blank');
      }
    },
  },
};
</script>

<style scoped>
/* Contenedor principal */
.container {
  background-color: #f9fafb;
  border: 2px solid #e5e7eb;
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

/* Inputs de archivos */
.file-input {
  display: block;
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.file-input:focus {
  outline: none;
  border-color: #3b82f6;
}

/* Botón de carga */
.upload-btn {
  display: block;
  width: 100%;
  padding: 12px;
  background-color: #3b82f6;
  color: #fff;
  text-align: center;
  font-size: 1rem;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.upload-btn:hover {
  background-color: #2563eb;
}

.upload-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

/* Barra de progreso */
.bg-green-500 {
  background-color: #10b981;
}

.bg-blue-500 {
  background-color: #3b82f6;
}

.bg-gray-300 {
  background-color: #e5e7eb;
}

/* Mensajes de éxito/error */
.text-green-600 {
  color: #16a34a;
}

.text-red-600 {
  color: #dc2626;
}

/* Botón de descarga */
.download-btn {
  padding: 12px;
  background-color: #4ade80;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.download-btn:hover {
  background-color: #3bbf6b;
}
</style>
