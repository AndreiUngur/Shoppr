from datetime import datetime
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from tables import Product, Cart, CartItem

from utils import db


class ProductObject(SQLAlchemyObjectType):
    """
    Maps to `Product` table in Database.
    """
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node, )


class CartObject(SQLAlchemyObjectType):
    """
    Maps to `Cart` table in Database.
    """
    class Meta:
        model = Cart
        interfaces = (graphene.relay.Node, )


class CartItemObject(SQLAlchemyObjectType):
    """
    Maps to `CartItem` table in Database.
    """
    class Meta:
        model = CartItem
        interfaces = (graphene.relay.Node, )


class Query(graphene.ObjectType):
    """
    Basic Query object.
    """
    node = graphene.relay.Node.Field()
    all_products = SQLAlchemyConnectionField(ProductObject)


class CreateProduct(graphene.Mutation):
    """
    Creates a Product.
    Used for administrative and testing purposes, as users shall not
    be allowed to create products.

    Arguments:
    title: Name of product.
    price: Price of product.
    inventory_count: Amount of product in stock.
    """
    class Arguments:
        title = graphene.String(required=True)
        price = graphene.Float(required=True)
        inventory_count = graphene.Int(required=True)

    product = graphene.Field(lambda: ProductObject)

    def mutate(self, _, title, price, inventory_count):
        product = Product.query.filter_by(title=title).first()
        if product:
            raise Exception("Product already exists in database.")
        product = Product(title=title, price=price, inventory_count=inventory_count)
        db.session.add(product)
        db.session.commit()

        return CreateProduct(product=product)

class FetchOneProduct(graphene.Mutation):
    """
    Fetches data regarding a product based on its title.

    Arguments:
    title: Name of product.
    """
    class Arguments:
        title = graphene.String(required=True)
    
    product = graphene.Field(lambda: ProductObject)
    
    def mutate(self, _, title):
        product = Product.query.filter_by(title=title).first()
        if not product:
            raise Exception("Product doesn't exist.")
        return FetchOneProduct(product=product)

class FetchAllProducts(graphene.Mutation):
    """
    Fetches all products created.

    Arguments:
    only_available_items: whether to return only items in stock.
    """
    class Arguments:
        only_available_items = graphene.Boolean()

    products = graphene.List(ProductObject)

    def mutate(self, _, only_available_items=False):
        products = []

        if only_available_items:
            products = Product.query.filter(Product.inventory_count > 0).all()
        else:
            products = Product.query.all()

        return FetchAllProducts(products=products)

class PurchaseProduct(graphene.Mutation):
    """
    Consume a product. This has been kept despite implementing the cart as
    some might prefer purchasing single products, and might find the cart to be an overhead.

    Arguments:
    title: Name of product to be purchased.
    funds: Available funds of user to be invested in product.
    """
    class Arguments:
        title = graphene.String(required=True)
        funds = graphene.Float(required=True)
    
    product = graphene.Field(lambda: ProductObject)
    
    def mutate(self, _, title, funds):
        purchased_product = Product.query.filter_by(title=title).filter(Product.inventory_count > 0).first()
        if not purchased_product:
            raise Exception("Product not in store")
        if funds < purchased_product.price:
            raise Exception("Insufficient funds.")
        purchased_product.inventory_count -=  1
        return PurchaseProduct(product=purchased_product)

class CreateCart(graphene.Mutation):
    """
    Creates a cart for a given user.

    Arguments:
    user: ID of user wishing to set up a cart.
    """
    class Arguments:
        user = graphene.Int(required=True)

    cart = graphene.Field(lambda: CartObject)

    def mutate(self, _, user):
        # We want to add unique carts. The `unique` key constraint returns
        # an exception that isn't as descriptive as this.
        cart = Cart.query.filter_by(user_id=user).first()
        if cart:
            raise Exception("Cart already exists for user.")
        cart = Cart(user_id=user, created_date=datetime.now(), total=0)
        db.session.add(cart)
        db.session.commit()

        return CreateCart(cart=cart)

class AddToCart(graphene.Mutation):
    """
    Adds a given product to the cart.

    Arguments:
    user: ID of user wishing to add the product.
    title: Name of product.
    quantity: Requested quantity of a given product.
    """
    class Arguments:
        user = graphene.Int(required=True)
        title = graphene.String(required=True)
        quantity = graphene.Int(required=True)

    cartitems = graphene.List(CartItemObject)

    def mutate(self, _, user, title, quantity):
        # The quantity must be at least zero, otherwise why add it to the cart.
        if quantity <= 0:
            raise Exception("Quantity must be at least 1.")

        # The product must be in stock, in the desired quantity.
        product = Product.query.filter_by(title=title).filter(Product.inventory_count >= quantity).first()
        if not product:
            raise Exception("Item not in stock in sufficient quantities.")

        # A cart must exist for the user.
        cart = Cart.query.filter_by(user_id=user).first()
        if not cart:
            raise Exception("Please create a cart!")

        # If the product is already in the cart, simply increase the quantity requested.
        current_items = CartItem.query.filter_by(cart_id=cart.id)
        for item in current_items:
            if item.product_id == product.id:
                # The new quantity must be valid, relative to the amount in stock.
                if item.quantity + quantity <= product.inventory_count:
                    item.quantity += quantity
                    cart.total += product.price
                    all_items = CartItem.query.filter_by(cart_id=cart.id).all()
                    return AddToCart(cartitems=all_items)
                else:
                    raise Exception(f"There are only {product.inventory_count} items of type {product.title} "
                                    f", but you have requested {item.quantity + quantity}")
        item = CartItem(product_id=product.id, cart_id=cart.id, quantity=quantity)
        db.session.add(item)
        db.session.commit()
        cart.total += product.price

        # Return the updated list of cart items to the user.
        all_items = CartItem.query.filter_by(cart_id=cart.id).all()
        return AddToCart(cartitems=all_items)


class CompleteCart(graphene.Mutation):
    """
    Process a transaction with the cart.
    In the event of a user wishing to purchase some available and some
    unavailable items, the system will ignore unavailable items but
    proceed with the purchase of available ones.

    Once a cart is completed, the user will receive the new state of
    the database for the purchased products.

    Arguments:
    user: User wishing to purchase cart items.
    funds: Money user is wishing to spend on the cart.
    """
    class Arguments:
        user = graphene.Int(required=True)
        funds = graphene.Float(required=True)

    products = graphene.List(ProductObject)

    def mutate(self, _, user, funds):
        # Ensure cart exists for user, we can't complete a cart
        # which doesn't exist.
        cart = Cart.query.filter_by(user_id=user).first()
        if not cart:
            raise Exception("Cart does not exist for user. Please create a cart.")

        # Evaluate the total cost of the cart
        cartitems = CartItem.query.filter_by(cart_id=cart.id).all()
        purchased_products = []
        for item in cartitems:
            product = Product.query.filter_by(id=item.product_id).filter(Product.inventory_count >= item.quantity).first()
            if not product:
                # The product is now out of stock, or in insufficient quantities.
                # We ignore it.
                continue
            purchased_products.append(product)

        # User didn't provide sufficient funds for their purchase
        if cart.total > funds:
            raise Exception(f"Insufficient funds. Cost is {cart.total} but you have {funds}.")

        # Remove products purchased from inventory
        for product in purchased_products:
            product.inventory_count -=  1

        # Delete cart items as well as cart.
        CartItem.query.filter_by(cart_id=cart.id).delete(synchronize_session=False)
        Cart.query.filter_by(id=cart.id).delete(synchronize_session=False)
        return CompleteCart(products=purchased_products)


class Mutation(graphene.ObjectType):
    """
    Defines all available mutations.
    """
    create_product = CreateProduct.Field()
    fetch_one_product = FetchOneProduct.Field()
    fetch_all_products = FetchAllProducts.Field()
    purchase_product = PurchaseProduct.Field()
    create_cart = CreateCart.Field()
    add_to_cart = AddToCart.Field()
    complete_cart = CompleteCart.Field()
