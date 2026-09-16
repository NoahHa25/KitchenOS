# KitchenOS — Founder Log

> A record of the decisions, milestones, failures, and lessons behind KitchenOS.

---

# 001 — The Idea

**Project:** KitchenOS
**Founder:** Nasser Haidar

KitchenOS started from a simple observation:

Restaurants operate on enormous amounts of operational data, but much of that data is disconnected.

Ingredients.

Purchases.

Inventory.

Waste.

Recipes.

Food costs.

Sales.

Staff operations.

The long-term idea is to connect these pieces into one system.

Not just another restaurant dashboard.

The goal is to build an operational foundation that can eventually understand what is happening inside a restaurant and help predict what will happen next.

That means AI comes later.

First, the underlying system has to be correct.

---

# 002 — The Inventory Engine

**Date:** 2026-09-16

Sprint 2 was a major milestone.

The goal was to move KitchenOS beyond basic CRUD and build a real inventory engine.

The system now understands inventory changes as business events rather than simply changing a number in a database.

The inventory engine supports concepts including:

- purchases
- usage
- waste
- adjustments
- stock movement history

The important architectural decision was that inventory mutations are transactional.

A stock update and its corresponding movement record must succeed together.

The system therefore follows:

```text
Operation
    ↓
Validate
    ↓
Update Inventory
    ↓
Create Movement
    ↓
Commit
```

If something fails:

```text
Rollback
```

This was one of the first moments where KitchenOS started feeling like an actual backend system rather than a university CRUD project.

---

# 003 — The First Real Inventory Verification

**Date:** 2026-09-16

We verified the inventory engine using a real stock transition.

Tomato inventory changed from:

```text
12.5 kg
```

to:

```text
22.5 kg
```

after a:

```text
+10 kg purchase
```

The important part wasn't the arithmetic.

The important part was verifying that the system could represent the operation through its transactional inventory model.

This became the first concrete verification that the stock movement engine was behaving as intended.

---

# 004 — Architecture Becomes a Priority

**Date:** 2026-09-16

After shipping the inventory engine, we stopped for a moment before immediately adding another feature.

That pause matters.

The project is becoming large enough that architecture decisions need to be written down instead of existing only in our heads.

KitchenOS now follows a layered backend architecture:

```text
FastAPI
   ↓
Services
   ↓
Repositories
   ↓
PostgreSQL
```

We also established several important principles:

- restaurant-scoped tenant isolation
- transactional inventory updates
- explicit stock movement records
- Decimal-safe quantities
- Alembic migrations
- separation of API, business logic, and persistence

This is the point where documentation became part of the engineering process.

---

# 005 — The Base Class Cleanup

During Sprint 2 we encountered a circular-import problem that temporarily resulted in two possible locations for the SQLAlchemy `Base`:

```text
app/models/base.py
app/db/base.py
```

The application is working, but having two potential sources of truth is unnecessary technical debt.

Sprint 3 therefore begins with a small cleanup:

```text
Remove:
app/db/base.py

Keep:
app/models/base.py
```

It is a small change.

But this is exactly the kind of small change that becomes expensive if ignored for months.

---

# 006 — Sprint 3 Begins

**Date:** 2026-09-16

# Recipes & Food Cost

Sprint 3 is where KitchenOS begins connecting inventory with the actual food a restaurant sells.

Before Sprint 3:

```text
Ingredients
      ↓
Inventory
```

After Sprint 3:

```text
Recipe
   ↓
Recipe Ingredients
   ↓
Inventory
```

This changes the nature of the system.

KitchenOS no longer only knows:

> "The restaurant has 12 kg of tomatoes."

It can start understanding:

> "A Margherita Pizza requires 0.20 kg of tomatoes."

That difference is the foundation for automated inventory consumption.

---

# 007 — The Margherita Test

The first conceptual recipe is a Margherita Pizza.

```text
Margherita Pizza

Tomato       0.20 kg
Mozzarella   0.15 kg
Basil        0.01 kg
Olive Oil    0.02 L
```

If one pizza is sold, the future inventory engine should be able to translate that sale into:

```text
Tomato       -0.20 kg
Mozzarella   -0.15 kg
Basil        -0.01 kg
Olive Oil    -0.02 L
```

And those changes should become inventory movement records.

This is the connection we're building:

```text
Sale
 ↓
Recipe
 ↓
Ingredient Quantities
 ↓
Inventory Consumption
 ↓
Movement Ledger
```

---

# 008 — Why Food Cost Comes After Inventory

Food cost could have been implemented as an isolated calculation.

We deliberately don't want that.

The goal is for food cost to emerge from the same data model that describes how the restaurant actually operates.

```text
Recipe
   +
Ingredient Cost
   +
Quantity
   ↓
Food Cost
```

This means a recipe can eventually answer:

```text
How much does this dish cost to produce?
```

And later:

```text
What is the margin?
```

And eventually:

```text
How is the cost changing over time?
```

The first question has to be correct before the later ones are useful.

---

# 009 — The Bigger Vision

The long-term KitchenOS pipeline is:

```text
Sales
  ↓
Recipes
  ↓
Ingredient Consumption
  ↓
Inventory History
  ↓
Demand Data
  ↓
Forecasting
  ↓
Purchase Recommendations
```

This is why we are deliberately building the boring parts first.

A forecasting model cannot fix bad inventory data.

AI cannot compensate for broken transaction logic.

A beautiful dashboard cannot compensate for an incorrect food-cost calculation.

The foundation has to be trustworthy.

---

# 010 — Engineering Philosophy

KitchenOS is being built with a few principles in mind.

### Build the foundation before the intelligence.

AI is the destination, not the foundation.

### Make important operations auditable.

If stock changes, we should be able to explain why.

### Prefer explicit architecture over cleverness.

The code should be understandable by another engineer.

### Treat migrations as part of the product.

The database schema is not an afterthought.

### Build like someone else will maintain it.

Even if the project is currently being built by one person, the architecture should be capable of supporting a team.

---

# 011 — Current Milestone

**Current status:** Sprint 3 — Recipes & Food Cost

Completed foundation:

```text
FastAPI
   ↓
Service Layer
   ↓
Repository Layer
   ↓
PostgreSQL
```

Operational domains currently established:

```text
Restaurant
Ingredients
Inventory
Stock Movements
```

Sprint 3 adds:

```text
Recipes
Recipe Ingredients
Food Cost
Recipe-driven Inventory Consumption
```

---

# 012 — What Comes Next

After recipes and food cost, KitchenOS will have a much more complete operational model:

```text
Restaurant
    │
    ├── Ingredients
    │       ↓
    │   Inventory
    │       ↓
    │   Stock Movements
    │
    └── Recipes
            ↓
       Recipe Ingredients
            ↓
       Ingredient Consumption
            ↓
       Food Cost
```

That gives us the foundation for the next stage:

```text
Sales Data
     ↓
Historical Consumption
     ↓
Demand Forecasting
     ↓
Smart Purchasing
```

The eventual goal is not to make KitchenOS another piece of restaurant software.

The goal is to make it a system that understands the restaurant's operations well enough to help run them.

---

# Founder Note

The interesting part of this project is not that every feature works on the first attempt.

It doesn't.

There have been broken imports, database problems, migration issues, Windows environment problems, server processes that refused to die, and plenty of debugging.

That's part of the process.

The important change is that we're no longer just writing isolated pieces of code.

We're designing a system.

Sprint by sprint, the pieces are starting to connect.

And now KitchenOS has something every serious product needs:

**a foundation.**
