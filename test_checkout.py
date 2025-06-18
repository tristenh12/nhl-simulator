import stripe

# Replace with your TEST secret key (starts with sk_test)
stripe.api_key = "REMOVED_SECRET"

# Replace with your actual TEST Price ID
TEST_PRICE_ID = "price_1RbUgFLh041OrJKozeN9eQJh"

session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
        'price': TEST_PRICE_ID,
        'quantity': 1,
    }],
    mode='payment',
    customer_email='testuser@example.com',  # Match an existing Supabase user if you want
    success_url='https://www.nhlwhatif.com/success',
    cancel_url='https://www.nhlwhatif.com/cancelled',
)

print("Test checkout created:")
print(session.url)
