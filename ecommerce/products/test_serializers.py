from django.test import TestCase
from .models import Category, Product, ProductVariant
from .serializers import ProductListSerializer, ProductDetailSerializer


class ProductSerializerTests(TestCase):
    def test_product_list_and_detail_serializers(self):
        cat = Category.objects.create(name='Toys', slug='toys')
        p = Product.objects.create(name='Toy Car', slug='toy-car', description='A car', short_description='Car', sku='TC-1', price=9.99, attributes={})
        p.categories.add(cat)
        pv = ProductVariant.objects.create(product=p, name='Red', sku='TC-1-RED', price=9.99, attributes={})

        list_ser = ProductListSerializer(instance=p)
        self.assertIn('name', list_ser.data)

        detail_ser = ProductDetailSerializer(instance=p)
        self.assertIn('variants', detail_ser.data)
