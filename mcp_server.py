"""
ProteinKart MCP Server — wraps the REST API as MCP tools for agents.

Tools exposed:
  - search_proteins: search/filter the catalog
  - get_protein_details: full product info by ID
  - place_order: create an order

Connects to the FastAPI backend running on port 8000.
Serves MCP over SSE on port 3000.



"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

# Backend API base URL
API_BASE = os.getenv("API_BASE_URL", "https://proteinkart-google-adk-431844677592.europe-west1.run.app")

mcp = FastMCP(
    name="ProteinKart",
    instructions="ProteinKart MCP server — search proteins, get details, place orders.",
    port=int(os.getenv("PORT", 3000)),
)


# ── Tool 1: Search Proteins ─────────────────────────────────
@mcp.tool()
async def search_proteins(
    query: str = "",
    type: str = "",
    brand: str = "",
    veg: bool = False,
    max_price: int = 0,
    min_rating: float = 0.0,
) -> str:
    """Search and filter protein products in the catalog.

    Args:
        query: Text search across product name, brand, flavour. Example: "chocolate whey".
        type: Protein type filter: whey, casein, isolate, plant, or blend.
        brand: Brand name filter, e.g. MuscleBlaze, Optimum Nutrition.
        veg: Set true to only show vegetarian products.
        max_price: Maximum price in INR (₹). 0 means no limit. Example: 3000.
        min_rating: Minimum star rating (0.0–5.0). Example: 4.0.
    """
    params = {}
    if query:
        params["q"] = query
    if type:
        params["type"] = type
    if brand:
        params["brand"] = brand
    if veg:
        params["veg"] = "true"

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/api/products", params=params)
        resp.raise_for_status()
        products = resp.json()

    if max_price > 0:
        products = [p for p in products if p["price"] <= max_price]
    if min_rating > 0:
        products = [p for p in products if p["rating"] >= min_rating]

    if not products:
        return "No products found matching your filters."

    lines = [f"Found {len(products)} product(s):\n"]
    for p in products:
        cost_per_g = round(p["price"] / (p["protein_per_serving"] * p["servings"]), 2)
        lines.append(
            f"--- \n"
            f"![{p['name']}]({p['image_url']})\n"
            f"**[ID:{p['id']}] {p['name']}** — {p['brand']}\n"
            f"Price: ₹{p['price']} | Rating: {p['rating']}★\n"
            f"In Stock: {'✅' if p['in_stock'] else '❌'}\n"
        )
    return "\n".join(lines)


# ── Tool 2: Get Protein Details ──────────────────────────────
@mcp.tool()
async def get_protein_details(product_id: int) -> str:
    """Get full details of a specific protein product by its ID, including product image.

    Args:
        product_id: The product ID (use search_proteins to find IDs).
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/api/products/{product_id}")
        if resp.status_code == 404:
            return f"Product with ID {product_id} not found."
        resp.raise_for_status()
        p = resp.json()

    total_protein = p["protein_per_serving"] * p["servings"]
    cost_per_g = round(p["price"] / total_protein, 2)

    return (
        f"# {p['name']}\n"
        f"![Product Image]({p['image_url']})\n\n"
        f"**Brand:** {p['brand']} | **Type:** {p['type'].upper()} | **Flavour:** {p['flavour']}\n"
        f"**Weight:** {p['weight_kg']}kg | **Price:** ₹{p['price']}\n"
        f"**Protein:** {p['protein_per_serving']}g/serving | **Servings:** {p['servings']}\n"
        f"**Rating:** {p['rating']}★ ({p['rating_count']} reviews)\n"
        f"**Certified:** {'✅ Yes' if p['certified'] else '❌ No'} | **Veg:** {'🌱 Yes' if p['veg'] else '🔴 No'}\n"
        f"**Availability:** {'✅ In Stock' if p['in_stock'] else '❌ Out of Stock'}"
    )


# ── Tool 3: Place Order ─────────────────────────────────────
@mcp.tool()
async def place_order(
    product_id: int,
    quantity: int,
    customer_name: str,
    customer_email: str,
) -> str:
    """Place an order for a protein product.

    Args:
        product_id: The product ID to order.
        quantity: Number of units to order (must be > 0).
        customer_name: Full name of the customer.
        customer_email: Email for order confirmation.
    """
    payload = {
        "product_id": product_id,
        "quantity": quantity,
        "customer_name": customer_name,
        "customer_email": customer_email,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/api/orders", json=payload)
        if resp.status_code == 404:
            return "Product not found. Please check the product ID."
        if resp.status_code == 400:
            return resp.json().get("detail", "Order failed — product may be out of stock.")
        resp.raise_for_status()
        order = resp.json()

    return (
        f"✅ Order Placed!\n"
        f"Order ID: #{order.get('order_id', 'N/A')}\n"
        f"Product: {order.get('product', 'Protein Product')} ({order.get('brand', 'N/A')})\n"
        f"Quantity: {order.get('quantity', quantity)}\n"
        f"Total: ₹{order.get('total_price', 'N/A')}\n"
        f"Status: {order.get('status', 'placed')}\n"
        f"Confirmation will be sent to: {order.get('customer_email', customer_email)}"
    )



# ── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # If PORT is set, use SSE (for Cloud Run), else use STDIO (for local IDE testing)
    if os.getenv("PORT"):
        mcp.run(transport="sse")
    else:
        mcp.run()
