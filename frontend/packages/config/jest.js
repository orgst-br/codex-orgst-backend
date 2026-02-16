import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)

export default {
  testEnvironment: '@happy-dom/jest-environment',
  setupFilesAfterEnv: ['@testing-library/jest-dom'],
  transform: {
    '^.+\\.[jt]sx?$': ['babel-jest', { configFile: require.resolve('./babel.react-ts.cjs') }],
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
    '!src/**/*.stories.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 80,
      lines: 85,
      statements: 80,
    },
  },
}
