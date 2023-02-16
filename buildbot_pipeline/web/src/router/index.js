import { createRouter, createWebHashHistory } from 'vue-router'
import BuilderList from '../views/BuilderList.vue'
import Builder from '../views/Builder.vue'
import Build from '../views/Build.vue'
import WorkerList from '../views/WorkerList.vue'
import Worker from '../views/Worker.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'index',
      component: BuilderList,
    },
    {
      path: '/builders/:id',
      name: 'builder',
      component: Builder,
      props: true,
    },
    {
      path: '/builders/:builderid/builds/:number',
      name: 'build',
      component: Build,
      props: route => ({...route.params, tab: route.query.tab}),
    },
    {
      path: '/workers/',
      name: 'workers',
      component: WorkerList,
    },
    {
      path: '/workers/:id',
      name: 'worker',
      component: Worker,
      props: true,
    },
  ]
})

export default router
