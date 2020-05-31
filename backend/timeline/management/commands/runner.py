import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from obswebsocket import obsws, requests

from ...models import Live, Sequence


class Command(BaseCommand):
    help = 'OBS Timeline Runner'

    def __init__(self):
        self.ws = obsws(settings.OBS_HOST, settings.OBS_PORT, settings.OBS_PASS)
        self.signal = False

    def handle(self, *args, **options):
        self.ws.connect()
        print("Connected!")
        while True:
            try:
                time.sleep(1)
                now = timezone.now()
                live = Live.get()
                if not live.active_show:
                    continue
                if not live.active_sequence:
                    s = Sequence.objects.filter(show=live.active_show, target__lt=now).order_by('-target').first()
                    if not s:
                        s = Sequence.objects.filter(show=live.active_show).order_by('target').first()
                        if not s:
                            print("Show empty, cannot recover.")
                            live.active_show = None
                            live.save()
                            continue
                        if now < s.target:
                            print("Before first sequence of show. Switching to first one!")
                            self.switch_sequence(s)

                    if s.target + s.duration < now:
                        print("Show has finished, cannot recover.")
                        live.active_show = None
                        live.save()
                        continue
                    live.active_sequence = s
                    live.save()
                    print("Recovering at sequence: %s" % (s))

                if live.active_sequence.target + live.active_sequence.duration < now:
                    if live.active_sequence.wait_signal:
                        if not self.signal:
                            continue
                        self.signal = False
                        print("Got signal!")
                    print("Sequence ended: %s" % (live.active_sequence))
                    s = live.active_sequence.next()
                    if not s:
                        print("Show has finished!")
                        live.active_show = None
                        live.save()
                        continue

                    self.switch_sequence(s)
                    live.active_sequence = s
                    live.save()

            except KeyboardInterrupt:
                break
            except Exception as ex:
                print(ex)
        self.ws.disconnect()

    def switch_sequence(self, s):
        # TODO
        self.ws.call(requests.SetCurrentScene(s.scene_name))
