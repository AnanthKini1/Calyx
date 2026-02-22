import { createServer } from 'node:http'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { join, extname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const DIST = join(__dirname, 'dist')
const PORT = process.env.PORT || 8080

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.json': 'application/json',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
}

createServer((req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname
  let file = join(DIST, pathname)

  if (!existsSync(file) || statSync(file).isDirectory()) {
    file = join(DIST, 'index.html')
  }

  const type = MIME[extname(file)] || 'application/octet-stream'
  res.writeHead(200, { 'Content-Type': type })
  createReadStream(file).pipe(res)
}).listen(PORT, '0.0.0.0', () => {
  console.log(`Listening on http://0.0.0.0:${PORT}`)
})
