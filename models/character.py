const mongoose = require('mongoose');

const characterSchema = new mongoose.Schema({
  character: String,
  series: String,
  wishlist: Number,
  lastUpdated: Date
});

module.exports = mongoose.model('Character', characterSchema);
