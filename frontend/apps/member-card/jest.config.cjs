module.exports = async () => {
  const { default: baseConfig } = await import('@orgst/config/jest')
  return { ...baseConfig }
}
