import { registerApplication, start } from 'single-spa'
import { constructApplications, constructLayoutEngine, constructRoutes } from 'single-spa-layout'

// Carrega o template de layout
const routes = constructRoutes(
  (document.querySelector('#single-spa-layout') as HTMLTemplateElement) ??
    (() => {
      // Fallback: carrega o layout inline se nao achar no DOM
      const template = document.createElement('template')
      template.innerHTML = `
        <single-spa-router>
          <route default>
            <h1>Orgst</h1>
          </route>
        </single-spa-router>
      `
      return template
    })(),
)

const applications = constructApplications({
  routes,
  loadApp({ name }) {
    return System.import(name)
  },
})

const layoutEngine = constructLayoutEngine({ routes, applications })

// Registra cada aplicacao encontrada no layout
applications.forEach(registerApplication)

// Ativa o layout engine e inicia o Single-SPA
layoutEngine.activate()
start()
