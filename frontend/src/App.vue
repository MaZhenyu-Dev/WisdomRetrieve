<template>
  <RouterView v-slot="{ Component, route }">
    <Transition name="layout" mode="out-in" appear>
      <component :is="Component" :key="route.fullPath" />
    </Transition>
  </RouterView>
</template>

<script setup lang="ts">
import { RouterView } from "vue-router";
</script>
