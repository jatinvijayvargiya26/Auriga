const seatMap = document.querySelector('#seat-map');
const calculateButton = document.querySelector('#calculate');
const errorBox = document.querySelector('#error');
const emptyReceipt = document.querySelector('#empty-receipt');
const receipt = document.querySelector('#receipt');
const movieSelect = document.querySelector('#movie');
const showDateInput = document.querySelector('#show-date');
const newDayButton = document.querySelector('#new-day');

const tierPrices = { Silver: 20000, Gold: 30000, Recliner: 50000 };
const selectedSeats = new Set();
let seatData = new Map();
let bookedSeats = new Set();

function localDate(offset = 0) {
  const current = new Date();
  current.setDate(current.getDate() + offset);
  return current.toISOString().slice(0, 10);
}

showDateInput.value = localStorage.getItem('cinevista-show-date') || localDate();

function setText(id, value) {
  const element = document.querySelector(`#${id}`);
  if (element) element.textContent = value;
}

function money(paise) {
  return `${Math.floor(paise / 100)}.${String(paise % 100).padStart(2, '0')}`;
}

function roundedPercentage(paise, basisPoints) {
  return Math.floor((paise * basisPoints + 5000) / 10000);
}

function calculateEstimate() {
  const baseTotal = [...selectedSeats].reduce((total, seatId) => (
    total + tierPrices[seatData.get(seatId).tier]
  ), 0);
  const festivalDiscount = Math.min(10000, baseTotal);
  const afterFestival = baseTotal - festivalDiscount;
  const memberDiscount = document.querySelector('input[name="membership"]:checked')?.value === 'Member'
    ? Math.min(roundedPercentage(afterFestival, 1000), 5000, afterFestival)
    : 0;
  const subtotal = afterFestival - memberDiscount;
  const fee = selectedSeats.size * 300;
  const gst = roundedPercentage(subtotal + fee, 1800);
  return { total: subtotal + fee + gst };
}

function updateSelectionSummary() {
  const ids = [...selectedSeats].sort();
  setText('selected-seats', ids.length ? ids.join(', ') : 'No seats selected');
  setText('selected-count', `${ids.length} ${ids.length === 1 ? 'ticket' : 'tickets'}`);
  setText('live-total', money(calculateEstimate().total));
  document.querySelectorAll('.seat').forEach((seatButton) => {
    seatButton.classList.toggle('is-selected', selectedSeats.has(seatButton.dataset.seat));
    seatButton.setAttribute('aria-pressed', selectedSeats.has(seatButton.dataset.seat));
  });
}

function toggleSeat(seatId) {
  if (bookedSeats.has(seatId)) return;
  if (selectedSeats.has(seatId)) selectedSeats.delete(seatId);
  else selectedSeats.add(seatId);
  errorBox.hidden = true;
  updateSelectionSummary();
}

function renderSeatMap(seats) {
  seatMap.innerHTML = '';
  const rows = [...new Set(seats.map((seat) => seat.row))];
  rows.forEach((row) => {
    const rowSeats = seats.filter((seat) => seat.row === row);
    const rowElement = document.createElement('div');
    rowElement.className = 'seat-row';
    rowElement.innerHTML = `<span class="row-label">${row}</span><div class="seat-cluster"></div>`;
    const cluster = rowElement.querySelector('.seat-cluster');
    rowSeats.forEach((seat, index) => {
      if (index === 4) cluster.insertAdjacentHTML('beforeend', '<span class="seat-aisle" aria-hidden="true"></span>');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `seat seat-${seat.tier.toLowerCase()}${seat.status === 'booked' ? ' is-booked' : ''}`;
      button.dataset.seat = seat.id;
      button.textContent = seat.number;
      button.title = seat.status === 'booked' ? 'Already Booked' : `${seat.tier} seat ${seat.id}`;
      button.disabled = seat.status === 'booked';
      button.setAttribute('aria-label', `${seat.tier} seat ${seat.id}${seat.status === 'booked' ? ', already booked' : ''}`);
      button.addEventListener('click', () => toggleSeat(seat.id));
      cluster.appendChild(button);
    });
    seatMap.appendChild(rowElement);
  });
}

async function loadSeats() {
  localStorage.setItem('cinevista-show-date', showDateInput.value);
  selectedSeats.clear();
  const response = await fetch(`/api/seats?date=${encodeURIComponent(showDateInput.value)}`);
  if (!response.ok) throw new Error('Unable to load the cinema seating plan');
  const data = await response.json();
  seatData = new Map(data.seats.map((seat) => [seat.id, seat]));
  bookedSeats = new Set(data.seats.filter((seat) => seat.status === 'booked').map((seat) => seat.id));
  renderSeatMap(data.seats);
  updateSelectionSummary();
}

function renderReceipt(data) {
  emptyReceipt.hidden = true;
  receipt.hidden = false;
  document.querySelector('#receipt-id').textContent = 'CONFIRMED';
  setText('receipt-number', data.receipt_number);
  setText('booking-date', data.booking_date);
  setText('booking-time', data.booking_time);
  setText('show-date-receipt', data.show_date);
  setText('receipt-customer-name', data.customer.name);
  setText('receipt-customer-contact', data.customer.email ? `${data.customer.mobile} · ${data.customer.email}` : data.customer.mobile);
  setText('receipt-customer-membership', data.customer.membership);
  setText('movie-name', data.movie.name);
  setText('movie-genre', data.movie.genre);
  setText('show-time', data.movie.show_time);
  setText('payment-status', 'Booking confirmed');
  setText('experience-label', data.movie.experience);
  document.querySelector('#experience-icon').textContent = experienceIcon(data.movie.genre);
  setText('ticket-count', `${data.ticket_count} ${data.ticket_count === 1 ? 'ticket' : 'tickets'}`);
  setText('receipt-seats', data.seats.seats.map((seat) => seat.id).join(', '));
  setText('receipt-categories', Object.entries(data.seats.categories).map(([tier, ids]) => `${tier}: ${ids.join(', ')}`).join(' · '));
  setText('base-ticket-total', data.base_ticket_total);
  setText('festival-discount', data.festival_discount);
  setText('member-discount', data.member_discount);
  setText('discounted-subtotal', data.discounted_subtotal);
  setText('convenience-fee', data.convenience_fee);
  setText('gst', data.gst);
  setText('final-total', data.final_booking_total);
  document.querySelector('#line-items').innerHTML = data.line_items.map((item) => `
    <div class="line-item">
      <span>${item.name} <small>× ${item.quantity} · INR ${item.unit_price} each</small></span>
      <span>INR ${item.total}</span>
    </div>
  `).join('');
}

function experienceIcon(genre) {
  return { Action: '🔥', Comedy: '😄', Romance: '♥', Horror: '👻', Drama: '🎭', 'Sci-Fi': '✦', Animation: '✧', Thriller: '◈' }[genre] || '✦';
}

calculateButton.addEventListener('click', async () => {
  const membership = document.querySelector('input[name="membership"]:checked')?.value;
  const customer = {
    name: document.querySelector('#customer-name').value.trim(),
    mobile: document.querySelector('#customer-mobile').value.trim(),
    email: document.querySelector('#customer-email').value.trim(),
    membership,
  };
  if (!customer.name || !/^\d{10,12}$/.test(customer.mobile) || (customer.email && !/^\S+@\S+\.\S+$/.test(customer.email)) || !membership) {
    errorBox.textContent = !customer.name ? 'Please enter the customer full name.' : !/^\d{10,12}$/.test(customer.mobile) ? 'Mobile number must contain 10 to 12 digits.' : customer.email && !/^\S+@\S+\.\S+$/.test(customer.email) ? 'Please enter a valid email address.' : 'Please select Member or Non-Member.';
    errorBox.hidden = false;
    return;
  }
  if (!selectedSeats.size) {
    errorBox.textContent = 'Select at least one available seat before generating the bill.';
    errorBox.hidden = false;
    return;
  }
  errorBox.hidden = true;
  calculateButton.disabled = true;
  calculateButton.querySelector('span').textContent = 'Confirming booking...';
  try {
    const response = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seats: [...selectedSeats], customer, is_member: membership === 'Member', movie_id: movieSelect.value, show_date: showDateInput.value }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Unable to generate booking');
    renderReceipt(data);
    selectedSeats.forEach((seatId) => bookedSeats.add(seatId));
    selectedSeats.clear();
    data.seats.seats.forEach((seat) => { seatData.set(seat.id, { ...seat, status: 'booked' }); });
    renderSeatMap([...seatData.values()]);
    updateSelectionSummary();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  } finally {
    calculateButton.disabled = false;
    calculateButton.querySelector('span').textContent = 'Confirm booking / Generate bill';
  }
});

document.querySelectorAll('input[name="membership"]').forEach((input) => input.addEventListener('change', updateSelectionSummary));
document.querySelector('#print-receipt').addEventListener('click', () => window.print());
document.querySelector('#new-booking').addEventListener('click', () => {
  selectedSeats.clear();
  receipt.hidden = true;
  emptyReceipt.hidden = false;
  document.querySelector('#receipt-id').textContent = 'READY';
  updateSelectionSummary();
});

showDateInput.addEventListener('change', () => {
  errorBox.hidden = true;
  receipt.hidden = true;
  emptyReceipt.hidden = false;
  loadSeats().catch((error) => { errorBox.textContent = error.message; errorBox.hidden = false; });
});

newDayButton.addEventListener('click', () => {
  showDateInput.value = localDate(1);
  document.querySelector('#customer-name').value = '';
  document.querySelector('#customer-mobile').value = '';
  document.querySelector('#customer-email').value = '';
  document.querySelectorAll('input[name="membership"]').forEach((input) => { input.checked = false; });
  receipt.hidden = true;
  emptyReceipt.hidden = false;
  errorBox.hidden = true;
  loadSeats().catch((error) => { errorBox.textContent = error.message; errorBox.hidden = false; });
});

loadSeats().catch((error) => {
  errorBox.textContent = error.message;
  errorBox.hidden = false;
});
