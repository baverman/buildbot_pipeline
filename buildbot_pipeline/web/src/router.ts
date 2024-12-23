import { createRouter, createWebHashHistory } from 'vue-router'
import BuilderList from './views/BuilderList.vue'
import Builder from './views/Builder.vue'
import Build from './views/Build.vue'
import WorkerList from './views/WorkerList.vue'
import Worker from './views/Worker.vue'

function intParams(params: Record<string, unknown>, ...names: string[]): Record<string, unknown> {
    const result: Record<string, unknown> = {}
    for (const k in params) {
        const v = params[k]
        if (names.includes(k)) {
            result[k] = parseInt(v as string)
        } else {
            result[k] = v
        }
    }
    return result
}

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
            props: (route) => intParams(route.params, 'id'),
        },
        {
            path: '/builders/:builderid/builds/:number',
            name: 'build',
            component: Build,
            props: (route) => ({
                ...intParams(route.params, 'builderid', 'number'),
                tab: route.query.tab,
            }),
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
            props: (route) => intParams(route.params, 'id'),
        },
    ],
})

export default router
