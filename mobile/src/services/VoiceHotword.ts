import { EventEmitter } from 'events';

const emitter = new EventEmitter();

export function onHotword(fn: () => void) {
  emitter.on('hotword', fn);
  return () => emitter.off('hotword', fn);
}

export function triggerHotword() {
  emitter.emit('hotword');
}


