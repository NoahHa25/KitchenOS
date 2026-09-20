
$API = "http://localhost:8000"
$RID = "b05bc1ec-115b-45ad-b96b-9210b24f6d2f"

Write-Host ""
Write-Host "KitchenOS Demo Seed" -ForegroundColor Cyan
Write-Host "Restaurant: $RID"
Write-Host ""

function PostJson($path, $body) {
    Invoke-RestMethod `
        -Uri "$API$path" `
        -Method Post `
        -ContentType "application/json" `
        -Body ($body | ConvertTo-Json -Depth 10)
}

# --------------------------------------------------
# Ingredients
# --------------------------------------------------

Write-Host "Creating ingredients..."

$flour = PostJson "/ingredients" @{
    restaurant_id = $RID
    name = "Pizza Flour"
    unit = "kg"
    current_stock = 50
    minimum_stock = 10
    cost_per_unit = 1.20
}

$sauce = PostJson "/ingredients" @{
    restaurant_id = $RID
    name = "Tomato Sauce"
    unit = "L"
    current_stock = 20
    minimum_stock = 5
    cost_per_unit = 3.50
}

$cheese = PostJson "/ingredients" @{
    restaurant_id = $RID
    name = "Mozzarella"
    unit = "kg"
    current_stock = 15
    minimum_stock = 3
    cost_per_unit = 8.00
}

$pepperoni = PostJson "/ingredients" @{
    restaurant_id = $RID
    name = "Pepperoni"
    unit = "kg"
    current_stock = 10
    minimum_stock = 2
    cost_per_unit = 12.00
}

# --------------------------------------------------
# Recipes
# --------------------------------------------------

Write-Host "Creating recipes..."

$margherita = PostJson "/recipes" @{
    restaurant_id = $RID
    name = "Margherita Pizza"
    description = "Classic Italian pizza"
    selling_price = 12.50
    portion_size = 1
    portion_unit = "pizza"
    is_active = $true
}

$pepPizza = PostJson "/recipes" @{
    restaurant_id = $RID
    name = "Pepperoni Pizza"
    description = "Pepperoni with mozzarella"
    selling_price = 15.00
    portion_size = 1
    portion_unit = "pizza"
    is_active = $true
}

# --------------------------------------------------
# Recipe Ingredients
# --------------------------------------------------

Write-Host "Linking ingredients..."

PostJson "/recipes/$($margherita.id)/ingredients?restaurant_id=$RID" @{
    ingredient_id = $flour.id
    quantity = 0.30
} | Out-Null

PostJson "/recipes/$($margherita.id)/ingredients?restaurant_id=$RID" @{
    ingredient_id = $sauce.id
    quantity = 0.10
} | Out-Null

PostJson "/recipes/$($margherita.id)/ingredients?restaurant_id=$RID" @{
    ingredient_id = $cheese.id
    quantity = 0.20
} | Out-Null

PostJson "/recipes/$($pepPizza.id)/ingredients?restaurant_id=$RID" @{
    ingredient_id = $flour.id
    quantity = 0.30
} | Out-Null

PostJson "/recipes/$($pepPizza.id)/ingredients?restaurant_id=$RID" @{
    ingredient_id = $sauce.id
    quantity = 0.10
} | Out-Null

PostJson "/recipes/$($pepPizza.id)/ingredients?restaurant_id=$RID" @{
    ingredient_id = $cheese.id
    quantity = 0.20
} | Out-Null

PostJson "/recipes/$($pepPizza.id)/ingredients?restaurant_id=$RID" @{
    ingredient_id = $pepperoni.id
    quantity = 0.15
} | Out-Null

# --------------------------------------------------
# Orders
# --------------------------------------------------

Write-Host "Creating demo orders..."

PostJson "/orders" @{
    restaurant_id = $RID
    items = @(
        @{
            recipe_id = $margherita.id
            quantity = 2
            unit_price = 12.50
        }
    )
} | Out-Null

PostJson "/orders" @{
    restaurant_id = $RID
    items = @(
        @{
            recipe_id = $pepPizza.id
            quantity = 1
            unit_price = 15.00
        }
    )
} | Out-Null

PostJson "/orders" @{
    restaurant_id = $RID
    items = @(
        @{
            recipe_id = $margherita.id
            quantity = 1
            unit_price = 12.50
        },
        @{
            recipe_id = $pepPizza.id
            quantity = 2
            unit_price = 15.00
        }
    )
} | Out-Null

Write-Host ""
Write-Host "Demo data created successfully!" -ForegroundColor Green
Write-Host ""