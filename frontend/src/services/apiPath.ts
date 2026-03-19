function splitPath(path: string): { pathname: string; suffix: string } {
  const source = String(path || '').trim() || '/'
  const queryIndex = source.search(/[?#]/)
  if (queryIndex < 0) {
    return { pathname: source, suffix: '' }
  }
  return {
    pathname: source.slice(0, queryIndex) || '/',
    suffix: source.slice(queryIndex),
  }
}

export function getPathVariants(path: string): string[] {
  const { pathname, suffix } = splitPath(path)
  const variants = [pathname]

  if (pathname.endsWith('/')) {
    variants.push(pathname.slice(0, -1) || '/')
  } else {
    variants.push(`${pathname}/`)
  }

  return [...new Set(variants.map((variant) => `${variant}${suffix}`))]
}
