from django.urls import reverse
from rest_framework.test import APITestCase
from products.models import Product, Category


class ProductPaginationTests(APITestCase):
    def setUp(self):
        cat = Category.objects.create(name='Cat', slug='cat')
        # create 30 products
        objs = []
        for i in range(30):
            p = Product(
                name=f'Product {i}',
                slug=f'product-{i}',
                description='d',
                short_description='s',
                sku=f'SKU{i}',
                price=10,
            )
            objs.append(p)
        Product.objects.bulk_create(objs)
        # m2m after bulk
        for p in Product.objects.all():
            p.categories.add(cat)

    def test_custom_page_size(self):
        url = reverse('product-list') + '?page_size=5'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 5)
        self.assertIn('count', resp.data)

    def test_max_page_size_enforced(self):
        url = reverse('product-list') + '?page_size=500'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # should cap at 100 (max_page_size)
        self.assertLessEqual(len(resp.data['results']), 100)