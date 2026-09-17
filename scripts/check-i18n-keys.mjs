import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import ts from 'typescript'

const root = process.cwd()
const catalogPath = path.join(root, 'src', 'i18n', 'catalog.ts')
const localeNames = ['zh-CN', 'ja-JP', 'en-US']
const source = fs.readFileSync(catalogPath, 'utf8')
const sourceFile = ts.createSourceFile(catalogPath, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
let catalogNode

function visit(node) {
  if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === 'catalog') {
    catalogNode = node.initializer
  }
  ts.forEachChild(node, visit)
}
visit(sourceFile)

if (!catalogNode || !ts.isObjectLiteralExpression(catalogNode)) {
  throw new Error('Unable to locate the catalog object in src/i18n/catalog.ts')
}

function propertyName(property) {
  if (ts.isStringLiteral(property.name) || ts.isIdentifier(property.name)) return property.name.text
  return undefined
}

function stringValue(node) {
  return ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) ? node.text : undefined
}

const keys = new Set()
const problems = []
for (const property of catalogNode.properties) {
  if (!ts.isPropertyAssignment(property)) continue
  const key = propertyName(property)
  if (!key) continue
  if (keys.has(key)) problems.push(`Duplicate translation key: ${key}`)
  keys.add(key)
  if (!ts.isObjectLiteralExpression(property.initializer)) {
    problems.push(`${key}: locale value must be an object`)
    continue
  }

  const translations = new Map()
  for (const translation of property.initializer.properties) {
    if (!ts.isPropertyAssignment(translation)) continue
    const locale = propertyName(translation)
    const value = stringValue(translation.initializer)
    if (locale) translations.set(locale, value)
  }
  for (const locale of localeNames) {
    const value = translations.get(locale)
    if (typeof value !== 'string' || value.trim() === '') problems.push(`${key}: missing ${locale} text`)
  }
  for (const locale of translations.keys()) {
    if (!localeNames.includes(locale)) problems.push(`${key}: unsupported locale ${locale}`)
  }

  const placeholders = localeNames.map((locale) => [
    locale,
    [...(translations.get(locale) || '').matchAll(/\{([A-Za-z0-9_]+)\}/g)].map((match) => match[1]).sort().join(','),
  ])
  if (new Set(placeholders.map(([, names]) => names)).size > 1) {
    problems.push(`${key}: interpolation placeholders differ (${placeholders.map(([locale, names]) => `${locale}=[${names}]`).join(' ')})`)
  }
}

const namespaces = new Set([...keys].map((key) => key.split('.')[0]))
const sourceRoot = path.join(root, 'src')
const files = []
function collect(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name)
    if (entry.isDirectory()) collect(fullPath)
    else if (/\.(ts|vue)$/.test(entry.name) && fullPath !== catalogPath) files.push(fullPath)
  }
}
collect(sourceRoot)

const usedKeys = new Set()
const explicitPatterns = [
  /\bt\(\s*["']([A-Za-z][A-Za-z0-9_-]*\.[A-Za-z0-9_.-]+)["']/g,
  /(?:i18nKey|labelKey|placeholderKey|hintKey)\s*:\s*["']([A-Za-z][A-Za-z0-9_-]*\.[A-Za-z0-9_.-]+)["']/g,
]
const assignedLiteralPattern = /(?:[:,]|=)\s*["']([A-Za-z][A-Za-z0-9_-]*\.[A-Za-z0-9_.-]+)["']/g
for (const file of files) {
  const contents = fs.readFileSync(file, 'utf8')
  for (const literalPattern of explicitPatterns) {
    for (const match of contents.matchAll(literalPattern)) {
      const key = match[1]
      if (namespaces.has(key.split('.')[0])) usedKeys.add(key)
    }
  }
  const codeContents = file.endsWith('.vue')
    ? [...contents.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map((match) => match[1]).join('\n')
    : contents
  for (const match of codeContents.matchAll(assignedLiteralPattern)) {
    const key = match[1]
    if (namespaces.has(key.split('.')[0])) usedKeys.add(key)
  }
}
for (const key of usedKeys) {
  if (!keys.has(key)) problems.push(`Translation key used by source but missing from catalog: ${key}`)
}

if (problems.length) {
  globalThis.console.error(`i18n key check failed with ${problems.length} problem(s):`)
  for (const problem of problems) globalThis.console.error(`- ${problem}`)
  process.exit(1)
}

globalThis.console.log(`i18n key check passed: ${keys.size} keys, ${localeNames.length} locales, ${usedKeys.size} statically referenced keys.`)
