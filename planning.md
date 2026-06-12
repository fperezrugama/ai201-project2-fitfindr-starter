# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

Description of FitFindr:

FitFindr helps users search for secondhand clothing items and understand how to style them with pieces from their existing wardrobe. When a user describes what they want, the agent first calls `search_listings(description, size, max_price)` to find matching listings from the mock dataset. If a listing is found, the selected item is stored in the session and passed to `suggest_outfit(new_item, wardrobe)`, then the outfit suggestion is passed to `create_fit_card(outfit, new_item)` to generate a short shareable caption.

If `search_listings` returns no matches, the agent should stop before calling the outfit or fit card tools. It should explain that no matching listings were found and suggest loosening the search, such as increasing the budget, removing the size filter, or using a broader item description.


---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches the mock secondhand listings dataset for items that match the user's requested clothing description, optional size, and maximum price. It filters listings by price and size when provided, then ranks matching items based on whether the request appears in the listing title, description, category, style tags, colors, or brand.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): The clothing item or style the user is searching for, such as "vintage graphic tee", "black plaform shoes", or "wide-leg pants".
- `size` (str): The requested size, such as "M", "L", "S/M", "W30", or None if the user does not specify a size.
- `max_price` (float): The maximum price the user is willing to pay, such as 30.0, or None if the user does not provide a budget.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
Returns a list of listing dictionaries sorted from most relevant to least relevant.
Each listing contains:

- id (str): Unique listing id.
- title (str): Item name.
- description (str): Detailed item description.
- category (str): One of tops, bottoms, outwear, shoes, or accessories.
- style_tags (list[str]): Style keywords such as vintage, grunge, y2k, streetwear, classic, or earth tones.
- size (str): Item size.
- condition (str): Item condition, such as excellent, good, or fair.
- price (float): Listing price.
- colors (list[str]): Colors in the item.
- brand (str or None): Brand name if availble, otherwise None.
- platform (str): Platform where the item is listed, such as depop, thredUp, or poshmark.

If no listings match, it returns an empty list [].

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If no listings match, the agent should stop the workflow before suggest_outfit or create_fit_card. It should store a clear error message in the session and tell the user to loosen the search by increasing the budget, removing the size filter, our using a broader description.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Suggests a complete outfit using selected thrift listing and the user's wardrobe. It uses wardrobe item names, categories, colors, style tags, and notes to recommend pieces that match the selected item. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected listing from search_listings. It should contain fields like title, description, category, style_tags, size, condition, price, colors, brand, and platform.
- `wardrobe` (dict): A wardrobe dictionary with an items key. Each wardrobe item includes id, name, category, colors, style_tags, and optional notes.

**What it returns:**
<!-- Describe the return value -->
Returns a string with a complete outfit suggestion. The response should mention the selected thrift item, one or more matching wardrobe pieces when available, the overall style or asthetic, and at least one practical styling tip.

Example return:
Pair the vintage graphic tee with your baggy straight-leg jeans and chunky white sneakers for a relaxed streetwear look. Add the vintage black demin jacket for more structure, and front-tuck the tee slightly to balance the oversized pieces. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, the tool should not crash. It should return general styling advice based on the selected item, such as suggesting relaxed denim, simple shoes, or a jacket that matches the item's color or aesthetic. If the selected item is missing or invalid, the tool should return a clear message saying it needs a valid item before suggesting an outfit. 

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Creates a short, shareable caption-style description for the final outfit. The fit card should sound casual and social-media ready instead of sounding like a product description.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion returned by suggest_outfit.
- `new_item`(dict): The selected thrift listing used in the outfit.

**What it returns:**
<!-- Describe the return value -->
Returns a short caption-style string that mentions the thrifted item, the platform or price when available, and the overall outfit vibe. The response should be different for different items and outfits.

Example return:
thrifted this faded graphic tee on depop for $24 and paired it with baggy denim + chunky sneakers for an easy worn-in streetwear fit 🖤

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

If the outfit input is empty or the selected item is missing, the tool should return a clear error message instead of crashing. Example: I need a complete outfit suggestion before I can create a fit card.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
Stretch tools will be added after the required agent works correctly.

Planned stretch features:

Retry logic with fallback: If search_listings returns no results, the agent can retry with loosened constraints, such as removing the size filter or increasing the max price.
Price comparison tool: A future compare_price(new_item, listings) tool can compare the selected item's price with similar listings in the dataset and estimate whether the price is low, fair, or high.
Style profile memory: A future memory feature can save the user's style preferences or wardrobe across sessions.

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
