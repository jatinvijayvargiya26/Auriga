let config;
const message = document.querySelector('#admin-message');

const moneyToPaise = (value) => Math.round(Number(value || 0) * 100);
const paiseToMoney = (value) => (Number(value || 0) / 100).toFixed(2);
const showMessage = (text, isError = false) => { message.textContent = text; message.className = `message ${isError ? 'is-error' : 'is-ok'}`; message.hidden = false; };

async function load() {
  const [configResponse, bookingsResponse, historyResponse] = await Promise.all([fetch('/api/config'), fetch('/api/bookings'), fetch('/api/admin/import-history')]);
  config = await configResponse.json();
  const bookings = (await bookingsResponse.json()).bookings;
  renderHistory((await historyResponse.json()).history || []);
  renderConfig(bookings);
}

function renderHistory(history) {
  document.querySelector('#import-history').innerHTML = history.length ? history.map((item) => `<tr><td>${item.filename}</td><td>${item.total_rows}</td><td>${item.imported}</td><td>${item.deduplicated}</td><td>${item.rejected}</td><td>${item.conflicts_count}</td><td>${item.status}</td></tr>`).join('') : '<tr><td colspan="7" class="empty">No imports yet.</td></tr>';
}

function renderImport(report) {
  const summary = document.querySelector('#import-summary');
  summary.hidden = false;
  summary.innerHTML = `<strong>${report.filename}</strong><span>${report.total_rows} rows</span><span>${report.imported} imported</span><span>${report.deduplicated} de-duplicated</span><span>${report.rejected} rejected</span><span>${report.conflicts_count} conflicts</span>`;
  document.querySelector('#import-rows').innerHTML = report.rows.map((row) => `<tr><td>${row.row_number}</td><td>${row.raw_seat_class || '—'}</td><td>${row.raw_price || '—'}</td><td>${row.normalized_seat_class || '—'}${row.normalized_price_paise == null ? '' : ` · INR ${paiseToMoney(row.normalized_price_paise)}`}</td><td><span class="import-status ${row.status.toLowerCase().replace('-', '')}">${row.status}</span></td><td>${row.reason}</td></tr>`).join('');
  document.querySelector('#apply-import').disabled = false;
  document.querySelector('#download-clean').hidden = false;
}

function renderConfig(bookings) {
  const settings = config.settings;
  document.querySelector('#member-rate').value = settings.member_discount_basis_points / 100;
  document.querySelector('#member-cap').value = paiseToMoney(settings.member_discount_cap_paise);
  document.querySelector('#fee').value = paiseToMoney(settings.convenience_fee_paise);
  document.querySelector('#gst').value = settings.gst_basis_points / 100;
  document.querySelector('#movies-table').innerHTML = config.movies.map((movie) => `<tr><td><strong>${movie.name}</strong><small>${movie.language} · ${movie.duration}</small></td><td>${movie.genre}</td><td><select data-movie-demand="${movie.id}"><option ${movie.demand === 'Highly Demanded' ? 'selected' : ''}>Highly Demanded</option><option ${movie.demand === 'Normal' ? 'selected' : ''}>Normal</option><option ${movie.demand === 'Low Demand' ? 'selected' : ''}>Low Demand</option></select></td><td><select data-movie-status="${movie.id}"><option ${movie.status === 'Active' ? 'selected' : ''}>Active</option><option ${movie.status === 'Coming Soon' ? 'selected' : ''}>Coming Soon</option><option ${movie.status === 'Sold Out' ? 'selected' : ''}>Sold Out</option></select></td>${['Silver', 'Gold', 'Recliner'].map((tier) => `<td><input class="price-input" data-movie-price="${movie.id}" data-tier="${tier}" type="number" min="0" value="${paiseToMoney(movie.prices[tier])}"></td>`).join('')}</tr>`).join('');
  document.querySelector('#offers-list').innerHTML = config.offers.map((offer) => `<div class="offer-row"><div><strong>${offer.name}</strong><small><input data-offer-start="${offer.id}" type="date" value="${offer.start_date}"> → <input data-offer-end="${offer.id}" type="date" value="${offer.end_date}"></small><small><input data-offer-discount="${offer.id}" type="number" min="0" value="${paiseToMoney(offer.discount_paise)}"> INR flat discount</small></div><label class="switch"><input data-offer-active="${offer.id}" type="checkbox" ${offer.active ? 'checked' : ''}><span></span></label></div>`).join('');
  document.querySelector('#shows-table').innerHTML = config.shows.map((show) => `<tr><td>${config.movies.find((movie) => movie.id === show.movie_id)?.name || show.movie_id}</td><td>${show.date}</td><td>${show.time}</td><td>${show.auditorium}</td><td>${Object.keys(show.price_overrides || {}).length ? 'Configured' : 'Default prices'}</td></tr>`).join('');
  document.querySelector('#categories-list').innerHTML = Object.entries(config.categories).map(([name, category]) => `<div class="category-row"><span class="category-dot ${name.toLowerCase()}"></span><div><strong>${name}</strong><small>Rows ${category.rows.join(', ')}</small><label>Seats / row <input data-category-seats="${name}" type="number" min="1" value="${category.seats_per_row}"></label></div><b>INR <input data-category-price="${name}" type="number" min="0" value="${paiseToMoney(category.price_paise)}"></b></div>`).join('');
  document.querySelector('#booking-count').textContent = bookings.length;
  document.querySelector('#stats').innerHTML = `<div><small>Movies</small><strong>${config.movies.length}</strong></div><div><small>Shows</small><strong>${config.shows.length}</strong></div><div><small>Active offers</small><strong>${config.offers.filter((offer) => offer.active).length}</strong></div><div><small>Bookings</small><strong>${bookings.length}</strong></div>`;
  document.querySelector('#bookings-table').innerHTML = bookings.length ? bookings.map((booking) => `<tr><td><strong>${booking.booking_id}</strong></td><td>${booking.customer.name}<small>${booking.customer.mobile}</small></td><td>${booking.movie.name}<small>${booking.show_date}</small></td><td>${booking.seats.seats.map((seat) => seat.id).join(', ')}</td><td><strong>INR ${booking.final_booking_total}</strong></td></tr>`).join('') : '<tr><td colspan="5" class="empty">No bookings in this session yet.</td></tr>';
}

function collect() {
  config.settings.member_discount_basis_points = Math.round(Number(document.querySelector('#member-rate').value) * 100);
  config.settings.member_discount_cap_paise = moneyToPaise(document.querySelector('#member-cap').value);
  config.settings.convenience_fee_paise = moneyToPaise(document.querySelector('#fee').value);
  config.settings.gst_basis_points = Math.round(Number(document.querySelector('#gst').value) * 100);
  document.querySelectorAll('[data-movie-demand]').forEach((input) => { config.movies.find((movie) => movie.id === input.dataset.movieDemand).demand = input.value; });
  document.querySelectorAll('[data-movie-status]').forEach((input) => { config.movies.find((movie) => movie.id === input.dataset.movieStatus).status = input.value; });
  document.querySelectorAll('[data-movie-price]').forEach((input) => { config.movies.find((movie) => movie.id === input.dataset.moviePrice).prices[input.dataset.tier] = moneyToPaise(input.value); });
  document.querySelectorAll('[data-offer-active]').forEach((input) => { config.offers.find((offer) => offer.id === input.dataset.offerActive).active = input.checked; });
  document.querySelectorAll('[data-offer-start]').forEach((input) => { config.offers.find((offer) => offer.id === input.dataset.offerStart).start_date = input.value; });
  document.querySelectorAll('[data-offer-end]').forEach((input) => { config.offers.find((offer) => offer.id === input.dataset.offerEnd).end_date = input.value; });
  document.querySelectorAll('[data-offer-discount]').forEach((input) => { config.offers.find((offer) => offer.id === input.dataset.offerDiscount).discount_paise = moneyToPaise(input.value); });
  document.querySelectorAll('[data-category-seats]').forEach((input) => { config.categories[input.dataset.categorySeats].seats_per_row = Number(input.value); });
  document.querySelectorAll('[data-category-price]').forEach((input) => { config.categories[input.dataset.categoryPrice].price_paise = moneyToPaise(input.value); });
}

document.querySelector('#save-all').addEventListener('click', async () => {
  try { collect(); const response = await fetch('/api/admin/config', { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(config) }); const result = await response.json(); if (!response.ok) throw new Error(result.error); config = result; showMessage('Configuration saved. Customer bookings now use the updated rules.'); renderConfig([]); } catch (error) { showMessage(error.message, true); }
});
document.querySelector('#add-movie').addEventListener('click', () => { const id = prompt('Movie ID, e.g. dune-part-two'); const name = prompt('Movie name'); if (!id || !name) return; config.movies.push({id, name, genre: 'Drama', language: 'English', duration: '2h 00m', demand: 'Normal', status: 'Active', experience: 'A great night out', active: true, prices: {Silver: 20000, Gold: 30000, Recliner: 50000}}); renderConfig([]); showMessage('New movie added. Save configuration to publish it.'); });
document.querySelector('#add-offer').addEventListener('click', () => { const name = prompt('Offer name'); if (!name) return; config.offers.push({id: name.toLowerCase().replace(/[^a-z0-9]+/g, '-'), name, start_date: new Date().toISOString().slice(0, 10), end_date: '2099-12-31', discount_paise: 0, discount_basis_points: 0, max_discount_paise: 0, active: true, applicable_movies: config.movies.map((movie) => movie.id), excluded_movies: {}}); renderConfig([]); showMessage('New offer added. Edit its JSON-backed settings in the configuration and save.'); });
document.querySelector('#preview-import').addEventListener('click', async () => {
  const file = document.querySelector('#price-import-file').files[0];
  if (!file) { showMessage('Choose a CSV price list first.', true); return; }
  try { const response = await fetch('/api/admin/price-import/preview', { method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ filename: file.name, content: await file.text() }) }); const report = await response.json(); if (!response.ok) throw new Error(report.error); renderImport(report); showMessage('Cleaned price list is ready for review.'); } catch (error) { showMessage(error.message, true); }
});
document.querySelector('#apply-import').addEventListener('click', async () => {
  if (!confirm('Apply only the validated, non-conflicting prices? Existing prices will be preserved for invalid/conflicting rows.')) return;
  try { const response = await fetch('/api/admin/price-import/apply', { method: 'PATCH' }); const result = await response.json(); if (!response.ok) throw new Error(result.error); document.querySelector('#apply-import').disabled = true; showMessage(`Price list applied: ${result.imported} imported, ${result.rejected} rejected, ${result.conflicts_count} conflicts.`); await load(); } catch (error) { showMessage(error.message, true); }
});
load().catch((error) => showMessage(error.message, true));
