<!-- Root component of the Cyber Panchayat application
     Serves as the main container that renders the appropriate view based on the current route.
     All page navigation and routing is handled through router-view. -->

<template>
  <div id="civic-app">
    <Toast />
    <router-view />
  </div>
</template>

<script setup>
import Toast from '@/components/Toast.vue'
</script>
