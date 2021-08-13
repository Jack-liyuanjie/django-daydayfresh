from django.contrib import admin
from django.core.cache import caches
from goods.models import GoodsType, IndexPromotionBanner, IndexTypeGoodsBanner, IndexGoodsBanner, GoodsImage, GoodsSKU, \
    Goods


# Register your models here.

class BaseModelAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        '''更新表中数据时调用'''
        super().save_model(request, obj, form, change)

        # 发出任务，让celery worker重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存数据
        caches.delete('index_page_data')

    def delete_model(self, request, obj):
        '''删除表中的数据时调用'''
        super().delete_model(request, obj)
        # 发出任务，让celery worker重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存数据
        caches.delete('index_page_data')


class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class GoodsImageAdmin(BaseModelAdmin):
    pass


class GoodsSKUAdmin(BaseModelAdmin):
    pass


class GoodsAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType,GoodsTypeAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(GoodsImage, GoodsImageAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(Goods, GoodsAdmin)

