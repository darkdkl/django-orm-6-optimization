from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count
from django.db.models import Prefetch


def serialize_post_optimized(post):

    tags = post.tags.all()
    return {
        "title": post.title,
        "teaser_text": post.text[:200],
        "author": post.author.username,
        "comments_amount": post.comments_count,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag_for_post(tag) for tag in tags],
        'first_tag_title': tags[0].title,
            }


def serialize_tag_for_post(tag):

    return {
        'title': tag.title,
        'posts_with_tag': tag.num_tags
            }


def serialize_tag(tag):

    return {
        'title': tag.title,
        'posts_with_tag': tag.popular
            }


def get_most_popular_posts(posts):

    most_popular_posts_ids = [post.id for post in posts]
    posts_with_comments = Post.objects.filter(
        id__in=most_popular_posts_ids).fetch_with_comments_count()
    ids_and_comments = posts_with_comments.values_list('id', 'comments_count')
    count_for_id = dict(ids_and_comments)
    # аналог dict, post['comments_count']=count_for_id[post.id]
    for post in posts:
        post.comments_count = count_for_id[post.id]
    return posts


def index(request):

    most_fresh_posts = Post.objects.most_fresh().prefetch_related('author')[:5]
    popular_posts = Post.objects.all().popular_posts().prefetch_related('likes').prefetch_related('author')[:5]
    most_popular_tags = Tag.objects.all().popular()[:5]
    context = {
        'most_popular_posts': [serialize_post_optimized(post) for post in get_most_popular_posts(popular_posts)],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
                }
    return render(request, 'index.html', context)


def post_detail(request, slug):

    post = Post.objects.count_likes_post_detail().get(slug=slug)
    comments = Comment.objects.select_related('author').filter(post=post)
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
                                    'text': comment.text,
                                    'published_at': comment.published_at,
                                    'author': comment.author.username,
                                    })

    related_tags = post.tags.count_tags()
    serialized_post = {
        "title": post.title,
        "text": post.text,
        "author": post.author.username,
        "comments": serialized_comments,
        'likes_amount': post.count_likes,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag_for_post(tag) for tag in related_tags],
                        }

    most_popular_tags = Tag.objects.count_tags().popular()[:5]
    popular_posts = Post.objects.all().popular_posts().prefetch_related('likes').prefetch_related('author')[:5]
    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag_for_post(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post_optimized(post) for post in get_most_popular_posts(popular_posts)],
                }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):

    tag = Tag.objects.get(title=tag_title)
    most_popular_tags = Tag.objects.all().popular()[:5]
    popular_posts = Post.objects.all().popular_posts().prefetch_related('likes').prefetch_related('author')[:5]
    related_posts = Post.objects.related_posts().prefetch_related('author')[:20]

    context = {
        "tag": tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        "posts": [serialize_post_optimized(post) for post in get_most_popular_posts(related_posts)],
        'most_popular_posts': [serialize_post_optimized(post) for post in get_most_popular_posts(popular_posts)],
                }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
