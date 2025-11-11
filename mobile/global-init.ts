// global-init.ts — must run before ANY other import
declare global {
  // eslint-disable-next-line no-var
  var ErrorUtils: { 
    setGlobalHandler?: (fn: (e: any, fatal?: boolean) => void) => void; 
    getGlobalHandler?: () => (e: any, fatal?: boolean) => void 
  } | undefined;
}

if (!global.ErrorUtils) {
  let _handler = (e: any, fatal?: boolean) => {
    // keep this minimal; don't import here
    // eslint-disable-next-line no-console
    console.error('[GlobalError]', fatal ? '(fatal)' : '', e);
  };
  global.ErrorUtils = {
    setGlobalHandler: fn => { if (typeof fn === 'function') _handler = fn; },
    getGlobalHandler: () => _handler,
  };
}

// should print true in Metro logs very early
console.log('[boot]', 'ErrorUtils ready?', !!global.ErrorUtils?.getGlobalHandler);

