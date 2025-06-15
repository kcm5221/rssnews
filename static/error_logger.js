(function setupErrorLogging(){
  const warn = console.warn;
  const error = console.error;

  console.warn = function(...args){
    warn.apply(console, args);
  };
  console.error = function(...args){
    error.apply(console, args);
  };

  window.addEventListener('error', (e) => {
    console.error('Script error:', e.message, '@', e.filename + ':' + e.lineno);
  });

  window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
  });
})();
