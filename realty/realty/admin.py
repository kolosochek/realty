from django.contrib import admin
from .models import RealtyAd, Image
from django.utils.html import escape
from django.utils.html import mark_safe


class RealtyAdAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('/static/css/admin.css',)
        }

    def phones_tag(self, obj):
        return mark_safe('<div class="b-phones-tag b-flex">{phones}</div>'.format(phones=obj.phones))

    def images_tag(self, obj):
        result = ''
        for image in obj.images.all():
            result += '<div class="b-image-wrapper">' \
                      '<a class="b-link" href="%s" target="_blank"><img class="b-image" src="%s" width="150" height="150" />%s</a>' \
                      '</div>' % (escape(image.url), escape(image.url), image.title if image.title else "no title")
        return mark_safe(result)

    def list_display_tag(self, obj):
        return mark_safe('<div class="b-images-tag-list b-flex"><img class="b-image" src="{url}" width="80" height="80" /><span class="b-title">{title}</span></div>'.format(url=obj.thumbnail, title=obj.title))

    images_tag.short_description = 'Images'
    images_tag.allow_tags = True
    phones_tag.short_description = 'Phones'
    phones_tag.allow_tags = True
    readonly_fields = ('images_tag', 'phones_tag')
    exclude = ('images', 'phones', )
    list_filter = ('date_posted', 'viber', 'telegram', 'whatsapp', )
    list_display = ['list_display_tag', ]
    search_fields = ['title', 'ad_author', 'price']

    def clear_image():
        img = cv2.imread("/home/noone/Downloads/saleme/test_with.jpg")
        alpha = 1.0
        beta = -100
        new = alpha * img + beta
        new = np.clip(new, 0, 255).astype(np.uint8)
        cv2.imwrite("/home/noone/Downloads/saleme/cleaned.png", new)





class ImageAdAdmin(admin.ModelAdmin):
    def thumbnail_tag(self, obj):
        return mark_safe('<img src="%s" width="80" height="80" />' % escape(obj.thumbnail))

    def image_tag(self, obj):
        return mark_safe('<img src="%s" width="80" height="80" />' % escape(obj.url))

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True

    fields = ('image_tag', )
    readonly_fields = ('image_tag', 'thumbnail_tag')

    list_display = ['thumbnail_tag', ]


admin.site.register(RealtyAd, RealtyAdAdmin)
admin.site.register(Image, ImageAdAdmin)
