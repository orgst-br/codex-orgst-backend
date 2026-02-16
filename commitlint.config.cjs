module.exports = {
  extends: ['@commitlint/config-conventional'],
  parserPreset: {
    parserOpts: {
      headerPattern:
        /^(feat|fix|chore|docs|refactor|test|build|ci|style)(\([a-zA-Z0-9\-_./]+\))?: (?:([A-Z0-9]+-[A-Z0-9]+) )?(.+)$/,
      headerCorrespondence: ['type', 'scope', 'reference', 'subject'],
    },
  },
  rules: {
    'type-enum': [2, 'always',
      ['feat', 'fix', 'chore', 'docs', 'refactor', 'test', 'build', 'ci', 'style']],
    'scope-empty': [0],
    'subject-empty': [2, 'never'],
    'header-max-length': [2, 'always', 200],
  },
}
