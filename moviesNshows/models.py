from django.db import models
import uuid
# Create your models here.


class Genre(models.Model):
    name = models.CharField("name",max_length=50,blank=False,null=False)

    def __str__(self) -> str:
        return self.name

class TvMedia(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True,
          primary_key=True, editable=False)
    media_type = models.CharField('Media type',max_length=40)
    original_title = models.CharField("Original title",max_length=500,null=False,blank=False)
    primary_title = models.CharField("Primary title",max_length=500,null=True)
    over18 = models.BooleanField('Over 18',default=False)
    startyear = models.IntegerField("Start year",null=True)
    length = models.PositiveIntegerField("Length in mins",default=0)
    genre = models.ManyToManyField(Genre,related_name="tvmedia")
    cover_image = models.ImageField("Cover Image", upload_to='moviesNshows_covers/', default='moviesNshows/default_cover.jpg')

    def __str__(self) -> str:
        return f"{self.original_title}:{self.length}:{self.startyear} -- {self.id}"