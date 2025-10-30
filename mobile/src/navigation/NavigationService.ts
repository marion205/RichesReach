let navigator: any = null;

export function setNavigator(ref: any) {
  navigator = ref;
}

export function navigate(name: string, params?: any) {
  if (navigator && navigator.navigate) {
    navigator.navigate(name as never, params as never);
  }
}


