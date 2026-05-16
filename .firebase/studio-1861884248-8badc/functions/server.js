const { onRequest } = require('firebase-functions/v2/https');
  const server = import('firebase-frameworks');
  exports.ssrstudio18618842488bad = onRequest({}, (req, res) => server.then(it => it.handle(req, res)));
  