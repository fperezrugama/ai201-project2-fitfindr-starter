# FitFindr 

FitFindr is a multi-tool AI agent for secondhand fashion. A user can describe a thrift item they are looking for, and the agent searches mock listings, chooses the best match, suggests an outfit using the user's wardrobe, and creates a short shareable fit card.

I also added stretch features: retry logic with fallback, price comparison, and style profile memory.

## Features

### Required Features
- search_listings()
- suggest_outfit()
- create_fit_card()
- Planning loop
- State management
- Error handling
- Multi-step workflow

### Stretch Features
- Retry logic with fallback
- Price comparison tool
- Style profile memory

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

Then open the local Gradio URL shown in the terminal.

Run tests:

```bash
pytest tests/
```

## Tool Inventory

### `search_listings(description, size, max_price)`

**Purpose:**
Searches the mock secondhand listings dataset.

**Inputs:**

* `description` (`str`): Clothing item or style request.
* `size` (`str | None`): Optional size filter.
* `max_price` (`float | None`): Optional price limit.

**Output:**
A list of matching listing dictionaries sorted by relevance. Returns `[]` if no listings match.

---

### `suggest_outfit(new_item, wardrobe)`

**Purpose:**
Suggests an outfit using the selected thrift item and the user's wardrobe.

**Inputs:**

* `new_item` (`dict`): Selected listing returned by `search_listings`.
* `wardrobe` (`dict`): Wardrobe dictionary containing an `items` list.

**Output:**
A non-empty outfit suggestion string. If the wardrobe is empty, the tool returns general styling advice instead of failing.

---

### `create_fit_card(outfit, new_item)`

**Purpose:**
Creates a short social-media-style caption for the outfit.

**Inputs:**

* `outfit` (`str`): Outfit suggestion returned by `suggest_outfit`.
* `new_item` (`dict`): Selected listing.

**Output:**
A short caption string. If the outfit is empty or invalid, the tool returns a clear error message.

---

### `compare_price(new_item, search_results)` *(Stretch Feature)*

**Purpose:**
Compares the selected item's price against similar listings.

**Inputs:**

* `new_item` (`dict`): Selected listing.
* `search_results` (`list[dict]`): Search results returned by `search_listings`.

**Output:**
A string explaining whether the selected item's price appears low, fair, or high compared with similar listings. If there are not enough comparable listings, the tool returns a message explaining that the comparison is limited.


## Planning Loop

The agent does not call all tools in a fixed sequence. Instead, it makes decisions based on the results returned by previous tools.

The workflow is:

1. Parse the user's query to extract the clothing description, size, and maximum price.
2. Call `search_listings(description, size, max_price)`.
3. If no results are found, retry once without the size filter.
4. If results are still empty, store an error message in the session and stop the workflow.
5. If results exist, store the top result as `selected_item`.
6. Call `compare_price(selected_item, search_results)` and store the result.
7. Call `suggest_outfit(selected_item, wardrobe)` using the selected listing and the user's wardrobe.
8. Call `create_fit_card(outfit_suggestion, selected_item)` using the generated outfit suggestion.
9. Return the completed session dictionary.

This planning loop ensures that the agent responds dynamically to different situations. For example, if no listing is found, the agent does not call `suggest_outfit()` or `create_fit_card()`. Instead, it returns a helpful error message explaining what the user can try next.

## State Management

The agent uses a session dictionary to pass information between tools and maintain context throughout a user interaction.

Important session keys include:

- `query`: Original user query.
- `parsed`: Parsed query information, including extracted size and maximum price.
- `search_results`: Results returned by `search_listings()`.
- `selected_item`: Top listing selected from the search results and passed to later tools.
- `wardrobe`: The user's selected wardrobe data.
- `outfit_suggestion`: Output returned by `suggest_outfit()`.
- `fit_card`: Output returned by `create_fit_card()`.
- `fallback_message`: Message stored when the retry search logic is triggered.
- `price_comparison`: Output returned by `compare_price()`.
- `style_profile`: Saved style preferences loaded from memory.
- `error`: Error message stored when the workflow stops early.

This approach allows information returned by one tool to be reused by later tools without requiring the user to re-enter it. For example, the `selected_item` returned from `search_listings()` is passed directly into `suggest_outfit()`, and the resulting `outfit_suggestion` is then passed into `create_fit_card()`.

## Error Handling

### No Listings Found

**Input tested:**

```bash
python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
```

**Output:**

```text
[]
```

**Full agent behavior:**

```text
No matching listings found. Try a broader description, a different size, or a higher max price.
```

The agent stops the workflow and leaves `selected_item`, `outfit_suggestion`, and `fit_card` as `None`.

---

### Empty Wardrobe

If the user has no wardrobe items, `suggest_outfit()` still returns general styling advice based on the selected item instead of crashing or returning an empty response.

---

### Empty Outfit Input

**Input tested:**

```bash
python -c "from tools import search_listings, create_fit_card; results = search_listings('vintage graphic tee', size=None, max_price=50); print(create_fit_card('', results[0]))"
```

**Output:**

```text
I need a complete outfit suggestion before I can create a fit card.
```

---

### Invalid Selected Item

**Input tested:**

```bash
python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe; print(suggest_outfit({}, get_example_wardrobe()))"
```

**Output:**

```text
I can't suggest an outfit because the selected thrift item is missing or invalid. Please choose a valid listing first.
```

---

## Stretch Features

### Retry Logic with Fallback

If the initial search returns no results, the agent automatically retries once without the size filter. If the retry succeeds, the workflow continues normally. If the retry also fails, the agent returns a clear error message and stops the workflow.

### Price Comparison

The `compare_price()` tool compares the selected listing against similar listings in the search results and reports whether the price appears low, fair, or high.

### Style Profile Memory

The agent stores simple style preferences in `data/style_profile.json`, including:

- `favorite_styles`
- `preferred_colors`
- `fit_preferences`

These preferences are loaded into the session and used as additional context during outfit generation.

## User Interface

FitFindr uses a Gradio interface that allows users to:
- Search for secondhand clothing items
- Choose between an example wardrobe and an empty wardrobe
- View the selected listing
- Receive an outfit suggestion
- Generate a shareable fit card

---

## Testing

I tested each tool individually and then tested the complete agent workflow.

### Run All Tests

```bash
pytest tests/
```

### Current Result

```text
9 passed
```

All required tool tests passed successfully, including normal behavior and failure-mode testing.

### Manual Application Tests

The Gradio application was manually tested using the following scenarios:

- `vintage graphic tee, max price 50`
- `designer ballgown, XXS, max price 5`
- `90s track jacket, size M, max price 60`
- Empty wardrobe mode
- Invalid maximum price input

These tests verified the normal workflow, retry logic, error handling behavior, state management, and stretch feature functionality.


## Spec Reflection

One way the project specification helped me was by requiring the design of the tools, planning loop, state management, and error handling before implementation. Writing the specifications in `planning.md` forced me to think about the exact inputs, outputs, and failure modes of each tool before writing code. This made development more structured because I could implement and test each tool independently during Milestone 3 before connecting them through the planning loop. As a result, debugging was significantly easier since I already knew what each component was expected to do and how data would flow between them.

One way the final implementation diverged from the original specification was the addition of multiple stretch features that expanded the agent's workflow beyond the initial three-tool design. The original plan focused on `search_listings()`, `suggest_outfit()`, and `create_fit_card()`. During development, I added retry logic with fallback, a price comparison tool, and style profile memory. The retry logic introduced an additional decision branch in the planning loop, allowing the agent to automatically retry searches without the size filter before returning an error. The price comparison feature added a fourth tool and an additional piece of session state, while style profile memory required persistent storage using a JSON file and integration of user preferences into outfit generation. These additions increased the complexity of the planning loop and state management system, but they improved the user experience by making the agent more resilient, informative, and personalized.

Another implementation difference was how query parsing was handled. The specification allowed multiple approaches, including using an LLM to extract parameters from the user's request. Instead, I implemented a lightweight parsing approach using regular expressions to extract size and price constraints directly from the query. This approach reduced latency, avoided unnecessary LLM calls, and kept the search process deterministic while still meeting the project requirements.


## AI Usage

### Example 1: Implementing `search_listings()`

I provided the Tool 1 specification from `planning.md`, including the tool's inputs, outputs, expected behavior, and failure handling requirements. The AI generated an initial implementation using `load_listings()` from the provided data loader. After testing the results, I revised the ranking logic so that direct matches such as *graphic tee* ranked higher than loosely related vintage items, resulting in more relevant search results.

### Example 2: Implementing the Planning Loop

I provided the **Planning Loop**, **State Management**, and **Architecture Diagram** sections from `planning.md` as input to the AI. The AI generated an initial implementation of `run_agent()` in `agent.py`. Before using the generated code, I reviewed and modified it to ensure that the no-results branch returned early, session state was stored correctly, retry fallback logic worked as intended, and tools were only called when appropriate rather than being executed unconditionally.

