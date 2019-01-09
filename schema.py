import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from tables import Product, Cart, CartItem
from datetime import datetime

class ProductObject(SQLAlchemyObjectType):
   class Meta:
       model = Product
       interfaces = (graphene.relay.Node, )

class CartObject(SQLAlchemyObjectType):
   class Meta:
       model = Cart
       interfaces = (graphene.relay.Node, )

class CartItemObject(SQLAlchemyObjectType):
   class Meta:
       model = CartItem
       interfaces = (graphene.relay.Node, )

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_products = SQLAlchemyConnectionField(ProductObject)

class CreateProduct(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        price = graphene.Float(required=True)
        inventory_count = graphene.Int(required=True)

    product = graphene.Field(lambda: ProductObject)

    def mutate(self, _, title, price, inventory_count):
        product = Product(title=title, price=price, inventory_count=inventory_count)
        db.session.add(product)
        db.session.commit()

        return CreateProduct(product=product)

class FetchOneProduct(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
    
    product = graphene.Field(lambda: ProductObject)
    
    def mutate(self, _, title):
        product = Product.query.filter_by(title=title).first()
        return FetchOneProduct(product=product)

class FetchAllProducts(graphene.Mutation):
    class Arguments:
        only_available_items = graphene.Boolean()

    products = graphene.List(ProductObject)

    def mutate(self, _):
        products = []

        if only_available_items:
            products = Product.query.filter(Product.inventory_count > 0).all()
        else:
            products = Product.query.all()

        return FetchAllProducts(products=products)

class PurchaseProduct(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        money = graphene.Float(required=True)
    
    product = graphene.Field(lambda: ProductObject)
    
    def mutate(self, _, title, money):
        purchased_product = Product.query.filter_by(title=title).filter(Product.inventory_count > 0).first()
        if not purchased_product:
            # TODO: Better exception handling
            raise Exception("Product not in store")
        if money < purchased_product.price:
            # TODO: Better exception handling
            raise Exception("Insufficient funds.")
        purchased_product.inventory_count -=  1
        return PurchaseProduct(product=purchased_product)

class CreateCart(graphene.Mutation):
    class Arguments:
        user = graphene.Int(required=True)

    cart = graphene.Field(lambda: CartObject)

    def mutate(self, _, uid):
        cart = Cart(user_id=uid, created_date=datetime.now())
        db.session.add(cart)
        db.session.commit()

        return CreateCart(cart=cart)

class AddToCart(graphene.Mutation):
    class Arguments:
        user = graphene.Int(required=True)
        title = graphene.String(required=True)
        quantity = graphene.Int(required=True)

    cartitems = graphene.List(CartItemObject)

    def mutate(self, _, user):
        product = Product.query.filter_by(title=title).filter(Product.inventory_count > 0).first()
        if not product:
            raise Exception("Item not in stock.")
        cart = Cart.query.filter_by(user=user).first()
        if not cart:
            raise Exception("Please create a cart!")
        item = CartItem(product_id=product.id, cart_id=cart.id, quantity=quantity)
        db.session.add(item)
        db.session.commit()

        all_items = CartItem.query.filter_by(cart_id=cart.id).all()
        return AddToCart(cartitems=all_items)

class CompleteCart(graphene.Mutation):
    class Arguments:
        user = graphene.Int(required=True)
        funds = graphene.Float(required=True)

    purchased_products = graphene.List(ProductObject)

    def mutate(self, _, user, funds):
        cart = Cart.query.filter_by(user=user).first()
        cartitems = CartItem.query.filter_by(cart_id=cart.id).all()
        total_cost = 0
        purchased_products = []
        for item in cartitems:
            product = Product.query.filter_by(id=item.product_id).filter(Product.inventory_count > 0).first()
            if not product:
                # The product is now out of stock ...
                continue
            total_cost += product.price
            purchased_products.append(product)

        if total_cost > funds:
            raise Exception("Insufficient funds.")
        for product in purchased_products:
            product.inventory_count -=  1
        return CompleteCart(purchased_products=purchased_products)


class Mutation(graphene.ObjectType):
    create_product = CreateProduct.Field()
    fetch_one_product = FetchOneProduct.Field()
    fetch_all_products = FetchAllProducts.Field()
    purchase_product = PurchaseProduct.Field()
    create_cart = CreateCart.Field()
    add_to_cart = AddToCart.Field()
    complete_cart = CompleteCart.Field()
