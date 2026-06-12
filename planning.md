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

The agent uses a session dictionary to track the current interaction and decide what to do next. It should not call every tool automatically. Instead, each tool call depends on whether the previous step suceeded.

Specific logic:

1. Start with the user's request, optional size, optional max price, and wardrobe.
2. Initialize a session dictionary with:
- query
- size
- max_price
- wardrobe
- search_results
- selected_item
- outfit_suggestion
- fit_card
- error
3. Call search_listings(description=query, size=size, max_price=max_price).
4. Store the returned list in session["search_results"].
5. If session["search_results"] is empty:
- Set session["error"] to a helpful no-results message.
- Keep session["selected_item"], session["outfit_suggestion"], and session["fit_card"] as None.
- Return the session immediately.
6. If search results exist:
- Select the first result as the best match.
- Store it in session["selected_item"].
7. Call suggest_outfit(new_item=session["selected_item"], wardrobe=session["wardrobe"]).
8. Store the returned outfit string in session["outfit_suggestion"].
9. If the outfit suggestion is empty or invalid:
- Set session["error"] to a helpful outfit-generation message.
- Keep session["fit_card"] as None.
- Return the session.
10. If the outfit suggestion is valid:
- Call create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"]).
11. Store the returned caption in session["fit_card"].
12. Return the completed session.

The workflow is done when either an error stops the process early or the session contains a selected listing, an outfit suggestion, and a fit card.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent stores data in a session dictionary during one user interaction. This makes the result from one tool available to the next tool without asking the user to repeat information.

The session tracks:

- query: the user's original clothing request.
- size: the requested size, or None if no size was provided.
- max_price: the user's budget, or None if no budget was provided.
- wardrobe: the wardrobe dictionary passed into the agent.
- search_results: the full list returned by search_listings.
- selected_item: the first and most relevant listing from search_results.
- outfit_suggestion: the string returned by suggest_outfit.
- fit_card: the string returned by create_fit_card.
- error: a message explaining what went wrong, or None if the workflow succeeds.

State flow:

1. search_listings returns a list of matching listing dictionaries.
2. The agent stores that list in session["search_results"].
3. The agent chooses session["search_results"][0] and stores it in session["selected_item"].
4. session["selected_item"] is passed into suggest_outfit.
5. The outfit response is stored in session["outfit_suggestion"].
6. session["outfit_suggestion"] and session["selected_item"] are passed into create_fit_card.
7. The final caption is stored in session["fit_card"].

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Store an error message in session["error"], stop the workflow immediately, and do not call suggest_outfit or create_fit_card. Show the user: "I could not find any listings that match that search. Try increasing your budget, removing the size filter, or using a broader description." |
| suggest_outfit | Wardrobe is empty | Return a general styling recommendation instead of crashing. Show the user: "Your wardrobe is empty right now, so I will style this generally: pair the item with relaxed denim, simple shoes, and a layer that matches its aesthetic." | 
|suggest_outfit | Selected item is missing or invalid | Return an error message explaining that a valid listing is required before an outfit can be generated. Store the message in session["error"] and stop the workflow before creating a fit card. |
| create_fit_card | Outfit input is missing or incomplete | Return a descriptive error string instead of raising an exception. Show the user: "I need a complete outfit suggestion before I can create a fit card." |
| create_fit_card | Selected item is missing | Return a descriptive error message explaining that listing information is required to generate the fit card. |

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

## Architecture

```text
User query
(description, optional size, optional max_price, wardrobe)
        |
        v
+----------------------------+
|        Planning Loop       |
|  decides next tool based   |
|  on current session state  |
+----------------------------+
        |
        v
+------------------------------------------------+
| search_listings(description, size, max_price)  |
+------------------------------------------------+
        |
        v
+-----------------------------+
| Were matching listings found?|
+-----------------------------+
        | Yes
        v
+-----------------------------------------------+
| Session State                                  |
| search_results = [listing1, listing2, ...]    |
| selected_item = search_results[0]             |
+-----------------------------------------------+
        |
        v
+---------------------------------------------+
| suggest_outfit(selected_item, wardrobe)      |
+---------------------------------------------+
        |
        v
+-------------------------------+
| Was an outfit suggestion made?|
+-------------------------------+
        | Yes
        v
+-----------------------------------------------+
| Session State                                  |
| outfit_suggestion = generated outfit text     |
+-----------------------------------------------+
        |
        v
+-----------------------------------------------------+
| create_fit_card(outfit_suggestion, selected_item)   |
+-----------------------------------------------------+
        |
        v
+----------------------------+
| Was a fit card generated?  |
+----------------------------+
        | Yes
        v
+-----------------------------------------------+
| Session State                                  |
| fit_card = generated caption                  |
+-----------------------------------------------+
        |
        v
+-----------------------------------------------+
| Final user output                              |
| 1. Selected listing                            |
| 2. Outfit suggestion                           |
| 3. Shareable fit card                          |
+-----------------------------------------------+


Error branch 1:
search_listings returns []
        |
        v
+-----------------------------------------------+
| Session State                                  |
| error = "No listings found. Try increasing     |
| budget, removing size, or broadening query."  |
| selected_item = None                           |
| outfit_suggestion = None                       |
| fit_card = None                                |
+-----------------------------------------------+
        |
        v
Return early to user.
Do not call suggest_outfit or create_fit_card.


Error branch 2:
suggest_outfit receives empty wardrobe
        |
        v
+-----------------------------------------------+
| Tool still returns general styling advice.     |
| Example: pair item with relaxed denim, simple |
| shoes, and a layer matching the item vibe.    |
+-----------------------------------------------+
        |
        v
Continue to create_fit_card if outfit text exists.


Error branch 3:
create_fit_card receives missing or empty outfit
        |
        v
+-----------------------------------------------+
| Return clear error string:                     |
| "I need a complete outfit suggestion before   |
| I can create a fit card."                     |
+-----------------------------------------------+
        |
        v
Return partial session to user.


Planned stretch feature branches:

Retry logic with fallback:
search_listings returns []
        |
        v
+-----------------------------------------------+
| Retry search with loosened constraints:        |
| 1. remove size filter                          |
| 2. or increase max_price slightly              |
| 3. or broaden description keywords             |
+-----------------------------------------------+
        |
        v
If retry finds results, continue normal flow.
If retry still fails, return helpful search error.


Price comparison tool:
After selected_item is stored
        |
        v
+-----------------------------------------------+
| compare_price(selected_item, search_results)  |
| estimates if price is low, fair, or high      |
| compared to similar listings in dataset       |
+-----------------------------------------------+
        |
        v
Store price_evaluation in session and include it
in the final user output.


Style profile memory:
Before suggest_outfit
        |
        v
+-----------------------------------------------+
| Load saved style preferences if available.     |
| Use preferences with wardrobe and selected     |
| item to make outfit suggestion more personal. |
+-----------------------------------------------+
```


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

For search_listings, I will use Claude or Codex and give it the Tool 1 specification from this planning.md, the listing fields from data_loader.py, and the instruction to use load_listings() instead of manually opening listings.json. I expect it to implement search_listings(description, size, max_price) so it filters by price and size when provided, searches across fields like title, description, category, style tags, colors, and brand, and returns matching listing dictionaries sorted by relevance. Before trusting the code, I will verify that it returns results for a normal query, returns [] for an impossible query, and respects the max price filter.

For suggest_outfit, I will give Claude or Codex the Tool 2 specification and the wardrobe schema from wardrobe_schema.json. I expect it to implement suggest_outfit(new_item, wardrobe) so it accepts the selected listing and a wardrobe dictionary, uses the Groq LLM to generate a useful outfit suggestion, and handles an empty wardrobe by returning general styling advice instead of crashing. I will verify it by testing with get_example_wardrobe() and get_empty_wardrobe().

For create_fit_card, I will give Claude or Codex the Tool 3 specification, the expected function signature, and examples of the caption style I want. I expect it to implement create_fit_card(outfit, new_item) so it uses the Groq LLM to generate a short social-media-style caption based on the selected item and outfit suggestion. I will verify that it returns a helpful error message when the outfit string is empty and that repeated calls can produce varied outputs.

For the planned stretch features, I will not ask the AI tool to implement them until the required three tools work correctly. After the required tools pass tests, I will update planning.md with stretch-specific specs for retry logic, price comparison, and style profile memory.


**Milestone 4 — Planning loop and state management:**

For the planning loop, I will use Claude or Codex and give it the Planning Loop section, the State Management section, the Error Handling table, and the ASCII Architecture diagram from this planning.md. I expect it to implement run_agent() in agent.py so the agent calls search_listings first, checks whether results exist, stores the selected item in the session, passes that item to suggest_outfit, stores the outfit suggestion, and then passes the outfit suggestion and selected item to create_fit_card.

Before trusting the generated code, I will check that the agent does not call all three tools unconditionally. I will verify that the no-results path returns early, stores a helpful message in session["error"], and leaves selected_item, outfit_suggestion, and fit_card as None.

For state management, I will verify the session dictionary after a successful query. I will check that session["search_results"] contains the listings returned by search_listings, session["selected_item"] is the same dictionary passed into suggest_outfit, session["outfit_suggestion"] is the same string passed into create_fit_card, and session["fit_card"] contains the final caption.

For app.py, I will give Claude or Codex the expected session keys and ask it to implement handle_query() so the Gradio interface displays the selected listing, outfit suggestion, fit card, or error message. I will verify this by running python app.py and testing one successful query and one no-results query.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

The agent receives the user's request and extracts the search criteria:

description = "vintage graphic tee"
size = None
max_price = 30.0
wardrobe = get_example_wardrobe()

The planning loop calls:

search_listings(
    description="vintage graphic tee",
    size=None,
    max_price=30.0
)

The tool searches the listings dataset and returns matching items such as:

Graphic Tee — 2003 Tour Bootleg Style ($24, Depop)
Vintage Band Tee — Faded Grey ($19, Depop)

The returned list is stored in:

session["search_results"]

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

The planning loop checks whether any results were returned.

Since the list is not empty, the first result is selected as the best match:

session["selected_item"] = session["search_results"][0]

The agent then calls:

suggest_outfit(
    new_item=session["selected_item"],
    wardrobe=session["wardrobe"]
)

Using the selected graphic tee and the example wardrobe, the tool generates an outfit suggestion such as:

"Pair the graphic tee with your baggy straight-leg jeans and chunky white sneakers for a relaxed streetwear look. Add the vintage black denim jacket for a stronger grunge aesthetic."

The response is stored in:

session["outfit_suggestion"]

**Step 3:**
<!-- Continue until the full interaction is complete -->

The planning loop verifies that an outfit suggestion was created.

It then calls:

create_fit_card(
    outfit=session["outfit_suggestion"],
    new_item=session["selected_item"]
)

The tool generates a short social-media-style caption such as:

"found this vintage graphic tee on depop for $24 and paired it with baggy denim + chunky sneakers for an easy everyday streetwear fit 🖤"

The caption is stored in:

session["fit_card"]

The completed session is returned.

**Final output to user:**
<!-- What does the user actually see at the end? -->

Selected Listing:

Graphic Tee — 2003 Tour Bootleg Style
Price: $24
Platform: Depop
Condition: Good

Outfit Suggestion:

"Pair the graphic tee with your baggy straight-leg jeans and chunky white sneakers for a relaxed streetwear look. Add the vintage black denim jacket for a stronger grunge aesthetic."

Fit Card:

"found this vintage graphic tee on depop for $24 and paired it with baggy denim + chunky sneakers for an easy everyday streetwear fit 🖤"

**Error Example:**

User query:

"I'm looking for a designer ballgown, size XXS, under $5."

The agent calls:

search_listings(
    description="designer ballgown",
    size="XXS",
    max_price=5.0
)

The tool returns:

[]

The planning loop stores:

session["error"]

with the message:

"I could not find any listings that match that search. Try increasing your budget, removing the size filter, or using a broader description."

The agent stops immediately and does not call suggest_outfit or create_fit_card.