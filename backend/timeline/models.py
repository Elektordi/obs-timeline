from datetime import timedelta
from django.db import models
from model_utils import FieldTracker


class Show(models.Model):
    name = models.CharField(max_length=100, null=False, unique=True)
    date = models.DateField(null=False)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return "[%s] %s" % (self.date, self.name)


class Sequence(models.Model):
    TYPE_SCENE = 1
    TYPE_MEDIA = 2
    TYPE_LIVEMEDIA = 3
    TYPES = [
        (TYPE_SCENE, "OBS Scene"),
        (TYPE_MEDIA, "Media file"),
        (TYPE_LIVEMEDIA, "Live media"),
    ]

    name = models.CharField(max_length=100, null=False)
    show = models.ForeignKey("Show", on_delete=models.CASCADE, related_name="sequences")
    type = models.PositiveSmallIntegerField(null=False, choices=TYPES)
    scene_name = models.CharField(max_length=100, blank=True)
    media_path = models.CharField(max_length=100, blank=True)
    target = models.DateTimeField(null=True)
    duration = models.DurationField(null=False, default=60)
    lock_duration = models.BooleanField(default=False)
    transition_effect = models.CharField(max_length=100, blank=True)
    wait_signal = models.BooleanField(default=False)

    tracker = FieldTracker()

    class Meta:
        unique_together = [['name', 'show']]
        ordering = ['target']

    def __str__(self):
        return "[%s] %s" % (self.target, self.name)

    def save(self, *args, **kwargs):
        # Chain update for following sequences
        n = self.next(True)
        if n:
            if self.lock_duration or self.tracker.has_changed('duration'):
                n.target = self.target + self.duration
                n.save()
            else:
                self.duration = n.target - self.target
                if self.duration < timedelta(seconds=1):
                    self.duration = timedelta(seconds=1)
                    n.target = self.target + self.duration
                    n.save()
        # Then save
        super().save(*args, **kwargs)

    def next(self, prev_target=False):
        if prev_target:
            target = self.tracker.previous('target')
        else:
            target = self.target
        return Sequence.objects.filter(show=self.show, target__gt=target).exclude(id=self.id).order_by('target').first()

    def previous(self, prev_target=False):
        if prev_target:
            target = self.tracker.previous('target')
        else:
            target = self.target
        return Sequence.objects.filter(show=self.show, target__lt=target).exclude(id=self.id).order_by('-target').first()


class Live(models.Model):
    active_show = models.ForeignKey("Show", null=True, on_delete=models.SET_NULL)
    active_sequence = models.ForeignKey("Sequence", null=True, on_delete=models.SET_NULL)

    @classmethod
    def get(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
