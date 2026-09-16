1. Problem Understanding
The main goal was to build a reliable cinema/multiplex booking and pricing system.
I divided the complete problem into smaller modules instead of implementing everything together.
The main modules were:
.Customer Details
.Movie & Show Details
.Seat Management
.Seat Selection
.Pricing & Discounts
.Convenience Fee & GST
.Bill/Receipt Generation
.Print Receipt
.Daily Seat Availability

                ┌─────────────────────┐
                │   Customer Details  │
                │ Name / Mobile / Email│
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Movie & Show Details│
                │ Date / Time / Genre │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │   Multiplex Seat Map│
                │ Silver / Gold /     │
                │ Recliner            │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │  Select Available   │
                │       Seats         │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Calculate Base Price│
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Festival Discount   │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Member Discount     │
                │      + Cap          │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │ Convenience Fee      │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │       GST           │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │    Final Receipt    │
                │ Seat + Customer +   │
                │ Complete Bill       │
                └──────────┬──────────┘
                           ↓
                ┌─────────────────────┐
                │    Print Receipt    │
                └─────────────────────┘
3. Seat Management Approach
I created a multiplex-style seating arrangement instead of taking seat numbers manually.
Seats are divided into:
Silver
Gold
Recliner
Each seat has its own unique seat ID such as:
A1
A2
B1
B2
Each seat has a status:
Available
Selected
Booked
Booked seats are disabled so that another customer cannot select them.
The customer can visually identify exactly which seats are available and which are already occupied.
Seat flow:>
Available
   ↓
Customer selects
   ↓
Selected
   ↓
Booking confirmed
   ↓
Booked
If the customer removes a selected seat:
Selected → Available

4. Customer Details
Added customer information before booking confirmation.
Details include:
Full Name
Mobile Number
Email
Membership status
Added validation so required information cannot be left empty.
These details are also displayed on the final receipt.
This makes the booking record more complete and realistic.

5. Pricing Calculation Approach

I followed a fixed pricing sequence to avoid calculation mistakes:
Base Ticket Amount
        ↓
Festival Flat Discount
        ↓
Member Percentage Discount
        ↓
Discounted Subtotal
        ↓
Convenience Fee
        ↓
GST
        ↓
Final Amount
Example:
Base Amount             ₹600
Festival Discount      -₹100
                        ----
                         ₹500

Member Discount 10%     -₹50
                        ----
                         ₹450

Convenience Fee          ₹60
                        ----
                         ₹510

GST                     ₹91.80
                        ----
Final Amount            ₹601.80

6. Handling Discount Cap
Member discount is percentage-based.
But the discount cannot exceed the configured maximum cap.

Example:
Calculated discount = ₹200
Maximum allowed      = ₹150

Actual discount      = ₹150
This prevents the discount from exceeding the business rule.

7. Accurate Money Calculation
Since this is a billing application, exact monetary calculation is important.
I avoided floating-point calculations for money wherever applicable.
Used precise decimal-based calculations.
Final values are maintained to two decimal places (paisa precision).
This prevents common floating-point errors in financial calculations.

8. Daily Seat Availability

One important real-world requirement was that today's bookings should not incorrectly block tomorrow's seats.

I therefore considered seat availability with respect to the show date.

Example:
16 September
A1 → Booked
A2 → Booked
B3 → Booked

17 September
A1 → Available
A2 → Available
B3 → Available
So each day's/show's seat availability is treated separately.
9. Refresh / New Day Approach

Added a Refresh / New Day concept.

When starting a new show day:

Current selected seats are cleared.
Temporary booking state is reset.
New show date is loaded.
Seat availability is loaded for that date.
Previous day's booked seats do not remain incorrectly booked.

I also distinguished between:
Browser Refresh
and
New Show Day
A browser refresh should not accidentally destroy valid current booking data, while starting a new day should intentionally load the new day's availability.
10. Receipt Generation

After successful booking, the system generates a professional multiplex receipt containing:

Multiplex name
Tagline
Booking ID
Customer name
Mobile number
Email
Membership status
Movie name
Movie genre
Show date
Show time
Selected seat numbers
Seat category
Ticket amount
Festival discount
Member discount
Convenience fee
GST
Final payable amount

This gives the customer a complete line-by-line breakup.

11. Movie Genre & Customer Experience
Added the movie genre to the booking and receipt.
The receipt can provide a small genre-based experience message.

For example:
Action     →  High Energy
Comedy     →  Feel Good
Romance    →  Romantic
Horror     →  Thrilling
Sci-Fi     →  Mind Bending
Drama      →  Emotional
Animation  →  Family Fun
The intention was to make the receipt feel more like a premium multiplex experience rather than just a basic invoice.
12. Print Receipt
Added a Print Receipt button.
Clicking it opens the browser's print dialog.
Only the receipt should be printed.

Other UI elements such as:

Buttons
Forms
Navigation
Seat map
Unnecessary webpage content

are hidden during printing.

13. Validation & Edge Cases

I considered several edge cases:

Empty customer name
Invalid mobile number
Invalid email
No seat selected
Sold-out seat selected
Duplicate seat selection
Invalid ticket quantity
Festival discount greater than ticket amount
Member discount greater than its maximum cap
Previous day's seats appearing booked on a new day

This makes the application more reliable in real-world usage.

14. Testing Approach

I tested the pricing engine using automated test cases.

The tests covered:

Normal booking
Multiple seat categories
Sold-out seats
Discount calculations
Member discount cap
Invalid booking conditions

The test execution showed:

Ran 4 tests
OK

So the core pricing logic was verified through automated testing.

15. What I Learned
How to break a real-world problem into smaller modules.
How to design a reusable pricing engine instead of hard-coding one scenario.
How seat availability and booking states can be managed.
How to connect frontend seat selection with backend/business pricing logic.
How discounts should be applied in a defined sequence.
Why exact decimal calculations are important for billing systems.
How to handle validation and edge cases.
How to maintain different seat availability for different show dates.
How to generate a customer-friendly invoice/receipt.
How to implement print-specific UI behavior.
How to use AI as an assistant for requirement analysis, architecture, implementation, debugging, and testing rather than blindly generating the complete project.


16. Overall Learning Flow
Understand Requirement
        ↓
Break into Modules
        ↓
Design Data & Business Rules
        ↓
Build Seat Management
        ↓
Build Pricing Engine
        ↓
Add Discounts + Fees + GST
        ↓
Add Customer Details
        ↓
Generate Detailed Receipt
        ↓
Add Print Functionality
        ↓
Add Daily Seat Management
        ↓
Test Edge Cases
        ↓
Review & Improve
Final Approach

My overall approach was to first understand the business rules, then build the pricing logic independently, integrate it with seat selection, and finally connect customer details, daily availability, receipt generation, and printing. This made the development process easier to understand, test, and extend for different cinemas and shows.