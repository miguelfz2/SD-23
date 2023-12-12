const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());

app.use(express.static('public'));

app.listen(8088, () => {
  console.log('ESCUCHANDO EN EL PUERTO 8088');
});

app.get('/', (req, res) => {
  res.sendFile(__dirname + 'public/index.html');
});
