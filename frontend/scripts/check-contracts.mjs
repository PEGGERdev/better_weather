import { execSync } from 'node:child_process'

const generatedFile = 'src/api/generated/backendContract.ts'

try {
  execSync('npm run gen:contracts', { stdio: 'inherit' })
  execSync(`git diff --exit-code -- ${generatedFile}`, { stdio: 'inherit' })
  console.log(`Contracts are in sync: ${generatedFile}`)
} catch {
  console.error(`Contract file out of sync: ${generatedFile}`)
  console.error('Run `npm run gen:contracts` and commit the updated generated file.')
  process.exit(1)
}
