from flask import Flask
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from flask_sqlalchemy import SQLAlchemy
import os
from flask_graphql import GraphQLView

# app initialization
app = Flask(__name__)
app.debug = True

basedir = os.path.abspath(os.path.dirname(__file__))

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql:///shopprdata'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

# Table
class Product(db.Model):
    __tablename__ = 'products'

    uuid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), index=True, unique=True)
    price = db.Column(db.Float)
    inventory_count = db.Column(db.Integer)
    
    def __repr__(self):
        return '<Product %r>' % self.title

# Graphql

class ProductObject(SQLAlchemyObjectType):
   class Meta:
       model = Product
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

    product = graphene.List(ProductObject)

    def mutate(self, _):
        products = Product.query.filter(Product.inventory_count > 0)
        return FetchAllProducts(product=products)

class PurchaseProduct(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        money = graphene.Float(required=True)
    
    product = graphene.Field(lambda: ProductObject)
    
    def mutate(self, _, title, money):
        purchased_product = Product.query.filter_by(title=title).filter(Product.inventory_count > 0).first()
        if not purchased_product:
            raise Exception
        purchased_product.inventory_count -=  1
        return PurchaseProduct(product=purchased_product)

class Mutation(graphene.ObjectType):
    create_product = CreateProduct.Field()
    fetch_one_product = FetchOneProduct.Field()
    fetch_all_products = FetchAllProducts.Field()
    purchase_product = PurchaseProduct.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)

@app.route('/')
def index():
    return '<p>Welcome to my store!</p>'

if __name__ == '__main__':
     app.run()

