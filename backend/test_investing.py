import investpy

try:
    print(investpy.technical.technical_indicators(name='THYAO', country='turkey', product_type='stock', interval='daily'))
except Exception as e:
    print(f"Error: {e}")
