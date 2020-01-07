from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import Prefetch


class RelatedPostsMixin():
    def related_posts(self):
        return self.prefetch_related(Prefetch('tags', queryset=Tag.objects.annotate(num_tags=Count('posts'))))   


class PostQuerySet(models.QuerySet, RelatedPostsMixin):
    def year(self, year):
        return self.filter(published_at__year=year).order_by('published_at')

    def popular_posts(self):
        return self.related_posts().annotate(popular_likes=Count('likes')).order_by('-popular_likes') 
        
    def fetch_with_comments_count(self):
        return self.annotate(comments_count=Count('comments'))

    def most_fresh(self):
        return self.related_posts().annotate(comments_count=Count('comments')).order_by('-published_at')
    
    def count_likes_post_detail(self):
        return self.select_related('author').annotate(count_likes=Count('likes'))


class TagQuerySet(models.QuerySet):

    def popular(self):
        return self.annotate(popular=Count('posts')).order_by('-popular')

    def count_tags(self):
        return self.annotate(num_tags=Count('posts'))


class Post(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    text = models.TextField("Текст")
    slug = models.SlugField("Название в виде url", max_length=200)
    image = models.ImageField("Картинка")
    published_at = models.DateTimeField("Дата и время публикации")
    objects = PostQuerySet.as_manager()
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name="Автор", limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User, related_name="liked_posts", verbose_name="Кто лайкнул", blank=True)
    tags = models.ManyToManyField(
        "Tag", related_name="posts", verbose_name="Теги")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField("Тег", max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ["title"]
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey("Post", related_name='comments',
                             on_delete=models.CASCADE, verbose_name="Пост, к которому написан")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Автор")

    text = models.TextField("Текст комментария")
    published_at = models.DateTimeField("Дата и время публикации")

    def __str__(self):
        return f"{self.author.username} under {self.post.title}"

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
