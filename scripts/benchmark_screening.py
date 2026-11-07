"""Reproducible CPU timing for the current bounded synthetic pair-screen loop."""
import argparse
import math
import platform
import time


def main():
    p=argparse.ArgumentParser(); p.add_argument('--objects',type=int,default=3); p.add_argument('--hours',type=int,default=24); p.add_argument('--step-minutes',type=int,default=5); a=p.parse_args()
    if not 2<=a.objects<=200 or not 1<=a.hours<=72 or not 1<=a.step_minutes<=60: p.error('objects 2..200; hours 1..72; step-minutes 1..60')
    objs=[((7000+i*10.,-60+i*13.,i*2.),(0.,7.5+i*.001,0.004*i)) for i in range(a.objects)]; n=a.hours*60//a.step_minutes
    start=time.perf_counter(); pairs=0
    for i,x in enumerate(objs):
      for y in objs[i+1:]:
        pairs+=1; best=math.inf
        for k in range(n+1):
          sec=k*a.step_minutes*60; d=math.sqrt(sum((x[0][q]+x[1][q]*sec-y[0][q]-y[1][q]*sec)**2 for q in range(3))); best=min(best,d)
    elapsed=(time.perf_counter()-start)*1000
    print({'python':platform.python_version(),'platform':platform.platform(),'objects':a.objects,'pairs':pairs,'horizon_hours':a.hours,'step_minutes':a.step_minutes,'samples_per_pair':n+1,'elapsed_ms':round(elapsed,3),'model':'constant velocity coarse sampling; timing only'})

if __name__=='__main__': main()
