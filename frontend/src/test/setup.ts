import '@testing-library/jest-dom';

// --- jsdom stubs required by layout/hooks used across components -----------

class ResizeObserverMock {
  private callback: ResizeObserverCallback;
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }
  observe(target: HTMLElement) {
    Object.defineProperty(target, 'clientWidth', { configurable: true, value: 640 });
    Object.defineProperty(target, 'clientHeight', { configurable: true, value: 300 });
    this.callback([], this as unknown as ResizeObserver);
  }
  unobserve() {}
  disconnect() {}
}

if (typeof (globalThis as any).ResizeObserver === 'undefined') {
  (globalThis as any).ResizeObserver = ResizeObserverMock;
}

const matchMediaMock = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: () => {},
  removeListener: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  dispatchEvent: () => false,
});

if (typeof (window as any).matchMedia !== 'function') {
  (window as any).matchMedia = matchMediaMock;
}