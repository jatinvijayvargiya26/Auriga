1. Requirement Understanding
I first analyzed the problem and divided the complete cinema system into smaller modules.
The main objective was to create a reliable, reusable and configurable cinema ticketing system.
Instead of hard-coding one movie or one cinema, I designed the system so that pricing, discounts, movies, shows and seats can be changed through configuration.
2. Overall System Flow
                    CINEMA TICKETING SYSTEM
                              │
                              ↓
                    Customer Details
                              │
                              ↓
                    Movie & Show Selection
                              │
                              ↓
                    Multiplex Seat Selection
                              │
                              ↓
                     Selected Seat Validation
                              │
                              ↓
                       Pricing Engine
                              │
              ┌───────────────┼────────────────┐
              ↓               ↓                ↓
        Base Price       Discounts          Charges
              │               │                │
              │        Festival Discount      │
              │        Member Discount        │
              │               │                │
              └───────────────┼────────────────┘
                              ↓
                     Convenience Fee
                              ↓
                             GST
                              ↓
                       Final Amount
                              ↓
                    Generate Bill/Receipt
                              ↓
                       Print Receipt
3. Modular Approach

I divided the application into separate logical areas:

Customer Management
Movie Management
Show Management
Seat Management
Pricing Engine
Discount Management
Festival Offers
Payment/Tax Calculation
Receipt Generation
Daily Seat Availability
Price List Import & Cleaning
Pricing Management UI

This made the application easier to understand, test and modify.

4. Multiplex Seat Arrangement
Added a realistic multiplex-style seating layout.
Seats are divided into different categories:
Silver
Gold
Recliner
Every seat has a unique seat number such as:
A1
A2
B1
B2
Added a screen indicator at the top.
Added aisles and row-based arrangement to make it look like a real cinema hall.
5. Seat Availability

Each seat can have different states:

🟢 Available
🔵 Selected
🔴 Booked

Flow:

Available
    ↓
Customer Selects
    ↓
Selected
    ↓
Booking Confirmed
    ↓
Booked
Booked seats cannot be selected again.
Customers can select and deselect available seats.
Selected seat count is automatically calculated.
6. Customer Details

Added customer information to the booking process:

Full Name
Mobile Number
Email
Membership Status

Validation was added so that invalid or missing information does not allow an incorrect booking.

The customer information is also displayed on the final receipt.

7. Movie & Show Details

The booking system supports:

Movie name
Genre
Show date
Show time
Movie demand level

Movies can be classified as:

Highly Demanded
Normal Demand
Low Demand

This information can be used by the operator while configuring pricing and discounts.

8. Pricing Calculation

The pricing calculation follows a fixed and transparent sequence:

Selected Seats
      ↓
Movie/Seat Price
      ↓
Base Ticket Amount
      ↓
Festival Discount
      ↓
Member Discount
      ↓
Discounted Subtotal
      ↓
Convenience Fee
      ↓
GST
      ↓
Final Payable Amount

This prevents confusion and makes the bill easy to explain.

9. Festival Discount
Added a flat festival discount.
Festival discounts can be configured instead of being permanently hard-coded.
Different festivals can have different discount rules.
The operator can decide which movies are eligible for a particular festival offer.

Example:

Diwali Offer
₹100 Discount

Movie A → Eligible
Movie B → Eligible
Movie C → Not Eligible
10. Highly Demanded Movies
Added an option to mark a movie as Highly Demanded.
The operator can decide whether a highly demanded movie should receive a discount.
If a movie is excluded from an offer, the receipt can clearly show the reason.

Example:

Festival Discount: ₹0
Reason: Highly Demanded Movie

This makes pricing transparent to the customer.

11. Member Discount

Added a percentage-based membership discount.

Example:

Member Discount = 10%
Maximum Cap = ₹150

If the calculated discount is higher than the cap:

Calculated = ₹200
Maximum = ₹150

Actual Discount = ₹150

This ensures the configured business rule is always respected.

12. Convenience Fee & GST

The convenience fee is calculated on a per-ticket basis.

Example:

3 tickets × ₹20
= ₹60

GST is then calculated according to the configured tax rate.

The system keeps the pricing breakdown visible to the customer.

13. Accurate Money Calculation
Billing requires accurate monetary calculations.
I avoided unreliable floating-point calculations for financial values.
Decimal-based calculations are used so the final bill is accurate to exactly two decimal places.
This ensures the system can correctly handle paisa-level calculations.
14. Professional Receipt

The generated receipt contains:

Multiplex name
Tagline
Booking ID
Customer details
Movie name
Genre
Show date
Show time
Selected seat numbers
Seat category
Base ticket amount
Festival discount
Member discount
Convenience fee
GST
Final payable amount

Example:

CineVista Multiplex
Your Movie. Your Moment.

Customer: Jatin
Movie: Interstellar
Genre: Sci-Fi
Show: 7:30 PM

Seats: B2, B3, B4

Base Amount       ₹750
Festival Discount -₹100
Member Discount   -₹65
Convenience Fee    ₹60
GST                ₹116.10

TOTAL              ₹761.10
15. Movie Genre Experience

The receipt also provides a small customer-friendly experience based on the movie genre.

Examples:

Action     → 🔥 High Energy
Comedy     → 😄 Feel Good
Romance    → ❤️ Romantic
Horror     → 👻 Thrilling
Drama      → 🎭 Emotional
Sci-Fi     → 🚀 Mind Bending
Animation  → ✨ Family Fun

The purpose was to make the receipt feel more like a premium multiplex experience instead of a plain invoice.

16. Print Receipt

Added a Print Receipt option.

When the customer clicks Print:

Browser print dialog opens.
Only the receipt is printed.
Seat map, buttons, forms and other unnecessary UI are hidden.
Receipt remains properly formatted for printing.
17. Daily Seat Availability

Seat availability is maintained according to the show/date.

Example:

16 September
A1 → Booked
A2 → Booked

17 September
A1 → Available
A2 → Available

This prevents previous day's bookings from incorrectly blocking seats for the next day.

18. Refresh / New Day

Added a New Day / Refresh concept.

When starting a new show day:

Current selected seats are cleared.
Temporary booking state is reset.
New date is loaded.
Correct seat availability is displayed.
Previous day's bookings do not incorrectly appear for the new day.

I also separated the concept of:

Browser Refresh

from:

New Show Day

so that a normal refresh does not accidentally destroy booking information.

19. Admin Pricing Management From Main Page

Instead of creating a completely separate admin website, I added a management option directly on the main page:

⚙️ Manage Pricing & Offers

When clicked, it opens a pricing/management panel.

The operator can access pricing controls without changing the source code.

20. Complete Pricing Control

The operator can configure:

Silver price
Gold price
Recliner price
Movie-specific pricing
Festival discount
Festival discount eligibility
Member discount percentage
Member discount cap
Convenience fee
GST/tax rate
Movie demand level

The main principle is:

The operator controls the business rules, while the pricing engine executes them.

21. Movie-Specific Pricing

Different movies can have different ticket prices.

Example:

Movie A
Silver     ₹180
Gold       ₹250
Recliner   ₹450

Movie B
Silver     ₹160
Gold       ₹230
Recliner   ₹420

This makes the pricing engine flexible for real cinema scenarios.

22. Festival & Movie Eligibility Management

The operator can configure which movies receive a festival discount.

Example:

Diwali Offer

Movie A      ✓
Movie B      ✓
Movie C      ✗ Highly Demanded
Movie D      ✓

This avoids applying the same discount blindly to every movie.

23. Complete Ticketing Control

The overall system provides control over:

Movies
Shows
Seats
Seat Categories
Movie Prices
Festival Offers
Member Discounts
Discount Caps
Convenience Fee
GST
Customer Bookings
Daily Availability

The goal was to make the application configurable for different cinema counters instead of creating a fixed one-time calculator.

24. The Twist – Messy Price List Import

A major additional requirement was to handle a messy real-world seat-class price list.

The input can contain:

Duplicate seat-class names
Different uppercase/lowercase
Extra spaces
Currency symbols
Different price formats
Blank values
Negative prices
Conflicting duplicate prices

Example:

Silver       180
silver       ₹180
SILVER       180.00
 Gold        Rs 250
Recliner     ₹450
Gold         -250
Silver

The system should not assume that the input data is already clean.

25. Messy Data Cleaning Flow
              Messy Price File
                     ↓
                  Import
                     ↓
              Clean Names
                     ↓
             Clean Price Format
                     ↓
                Validate
                     ↓
          ┌──────────┼──────────┐
          ↓          ↓          ↓
        Valid     Duplicate   Invalid
          ↓          ↓          ↓
       Import     De-duplicate Reject
          └──────────┼──────────┘
                     ↓
              Conflict Check
                     ↓
              Clean Price List
                     ↓
                Admin Review
                     ↓
              Apply New Prices
                     ↓
              Pricing Engine
26. Duplicate Handling

Different versions of the same seat class are treated as one:

Silver
silver
SILVER
 Silver

becomes:

Silver

But the system also reports that duplicate records were found instead of silently deleting them.

27. Price Format Cleaning

The system can normalize valid price formats such as:

180
180.00
₹180
₹180.00
Rs 180
INR 180

into a consistent format:

₹180.00
28. Invalid Data Rejection

Blank or invalid data is rejected.

Examples:

Silver → blank

→

Rejected: Missing price

And:

Gold → -250

→

Rejected: Negative price

Invalid data must never enter the pricing engine.

29. Conflicting Duplicate Prices

If the same seat class has different valid prices:

Silver → ₹180
silver → ₹200
SILVER → ₹180

the system identifies it as a conflict instead of randomly selecting a value.

The operator can review and decide the correct price.

30. Import Report

After processing the file, the system provides a summary:

Total Rows: 12

Successfully Imported: 3
De-duplicated: 4
Rejected: 4
Conflicts: 1

It also provides row-level information explaining:

What was imported
What was duplicate
What was rejected
Why something was rejected
Which records have conflicts

This makes the data-cleaning process transparent and auditable.

31. Clean Price List

After cleaning, only valid data is passed to the pricing engine.

Example:

Seat Class      Price

Silver          ₹180.00
Gold            ₹250.00
Recliner        ₹450.00

The admin can review the cleaned data before applying it.

32. Data-Driven Design

I avoided hard-coded business rules such as:

if movie == "Interstellar"
    price = 500

Instead, pricing and discount information is treated as configurable data.

This allows the same system to work with:

Different movies
Different shows
Different seat categories
Different festivals
Different prices
Different discount rules
33. Validation & Edge Cases

The system handles cases such as:

Empty customer name
Invalid mobile number
Invalid email
No seat selected
Sold-out seat
Duplicate seat selection
Invalid quantity
Negative price
Blank price
Negative discount
Discount exceeding cap
Festival date errors
Conflicting imported prices
Invalid price formats

This makes the system more reliable in real-world usage.

34. Testing Approach

I tested the system using different normal and edge cases.

Important tests included:

Normal booking
Multiple seat categories
Sold-out seats
Customer validation
Discount calculation
Member discount cap
Convenience fee
GST
Daily seat reset
Receipt generation
Seat numbers in receipt
Print functionality
Messy price import
Duplicate detection
Negative price rejection
Blank value rejection
Conflicting prices

Automated tests were also used to verify the pricing logic.

35. AI Assistant Usage

During development, I used the AI assistant in an iterative way:

Requirement Analysis
        ↓
Architecture
        ↓
Implementation
        ↓
Feature Addition
        ↓
Debugging
        ↓
Testing
        ↓
Review

Instead of asking AI to generate the entire application at once, I broke the work into smaller tasks and used AI to help with:

Understanding requirements
Designing the architecture
Implementing features
Finding bugs
Handling edge cases
Creating test cases
Improving UI
Reviewing implementation

This made the development process easier to understand and learn from.

36. Final Learning

Through this project, I learned:

How to convert a real-world problem into technical requirements.
How to divide a large application into modules.
How to design a reusable pricing engine.
How to manage seat availability and booking states.
How to implement configurable pricing.
How to apply discounts in a controlled sequence.
How to handle discount caps.
Why accurate monetary calculations are important.
How to design customer-friendly receipts.
How to implement print-specific UI.
How to manage date-based seat availability.
How to validate customer and pricing data.
How to clean messy real-world input data.
How to detect duplicates and conflicting records.
How to keep invalid data away from the pricing engine.
How to create transparent import reports.
How to make business rules configurable instead of hard-coded.
How to use an AI assistant effectively for analysis, development, debugging and testing.
37. Final Project Approach

The final approach can be summarized as:

Understand
   ↓
Break Requirements
   ↓
Design Modules
   ↓
Build Seat System
   ↓
Build Pricing Engine
   ↓
Add Discounts & Taxes
   ↓
Add Customer Details
   ↓
Add Receipt & Printing
   ↓
Add Daily Seat Management
   ↓
Add Pricing Management
   ↓
Import & Clean Messy Data
   ↓
Validate & Test
   ↓
Final Review
Final Objective

The project was developed as a complete, configurable and reusable cinema ticketing system where customers can select seats and receive a transparent bill, while the cinema operator can control movies, seats, prices, discounts, offers, fees, taxes and imported pricing data without modifying the source code.