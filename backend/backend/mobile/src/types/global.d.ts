// Global type declarations to resolve conflicts between libraries

// Suppress specific type conflicts
declare module '@types/node' {
  interface Require {
    (id: string): any;
  }
}

// Override conflicting types
declare global {
  // Override FormData to resolve conflicts
  interface FormData {
    append(name: string, value: string | Blob, fileName?: string): void;
    delete(name: string): void;
    get(name: string): FormDataEntryValue | null;
    getAll(name: string): FormDataEntryValue[];
    has(name: string): boolean;
    set(name: string, value: string | Blob, fileName?: string): void;
    forEach(callbackfn: (value: FormDataEntryValue, key: string, parent: FormData) => void, thisArg?: any): void;
  }

  // Override Blob to resolve conflicts
  interface Blob {
    readonly size: number;
    readonly type: string;
    slice(start?: number, end?: number, contentType?: string): Blob;
    arrayBuffer(): Promise<ArrayBuffer>;
    text(): Promise<string>;
    stream(): ReadableStream;
  }

  // Override global variables to resolve conflicts
  const require: NodeRequire;
  const module: NodeModule;
  const process: NodeJS.Process;
  const Buffer: typeof globalThis.Buffer;
  const global: typeof globalThis;
  const __dirname: string;
  const __filename: string;

  // React Native specific globals
  namespace NodeJS {
    interface Global {
      navigator: any;
      XMLHttpRequest: any;
      WebSocket: any;
      fetch: any;
      Headers: any;
      Request: any;
      Response: any;
      // URL and URLSearchParams are not fully supported in React Native
      // URL: any;
      // URLSearchParams: any;
    }
  }
}

// Export to make this a module
export {};
