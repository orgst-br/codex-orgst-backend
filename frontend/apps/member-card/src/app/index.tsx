import React from 'react'
import ReactDOMClient from 'react-dom/client'
import singleSpaReact from 'single-spa-react'

import { HomePage } from '../pages/HomePage'
import { AppProviders } from './providers'

function RootComponent() {
  return (
    <AppProviders>
      <HomePage />
    </AppProviders>
  )
}

const lifecycles = singleSpaReact({
  React,
  ReactDOMClient,
  rootComponent: RootComponent,
  errorBoundary(err: Error) {
    return <div>Erro no microfrontend member-card: {err.message}</div>
  },
})

export const { bootstrap, mount, unmount } = lifecycles
