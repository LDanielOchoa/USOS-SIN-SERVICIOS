<!-- src/App.vue -->
<template>
  <div id="app" class="min-h-screen flex flex-col items-center justify-center bg-gray-100">
    <h1 class="text-2xl font-bold mb-4">Carga de Archivos</h1>
    <FileUploader />
  </div>
</template>

<script>
import FileUploader from './components/FileUploader.vue';  // Asegúrate de que esta línea sea correcta

export default {
  components: {
    FileUploader,
  },
};
</script>

<style>
body {
  font-family: 'Arial', sans-serif;
}
</style>
