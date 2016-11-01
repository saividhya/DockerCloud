from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^name$', views.get_name, name='get_name'),
    url(r'^register$', views.register, name='register'),
    url(r'^$', views.index, name='index'),
    url(r'^login$', views.user_login, name='login'),
    url(r'^logout$', views.user_logout, name='logout'),
    url(r'^your-name/$', views.get_name, name='get_name'),
    url(r'^thanks/$', views.thanks, name='thanks'),
    url(r'^mainPage/$', views.getMainform, name='getMainform'),
    url(r'^addPage/$', views.getService, name='getService'),
    url(r'^modifyPage/$', views.modifyService, name='modifyService'),    
    url(r'^userHome/$', views.getUserHome, name='userHome'),
    url(r'^clusterHome/$', views.getClusterHome, name='clusterHome'),
    url(r'^addclusterPage/$', views.getaddclusterPage, name='addclusterPage'),
    url(r'^modifyclusterPage/$', views.getmodifyclusterPage, name='modifyclusterPage'),
    url(r'^service/add/$', views.getService, name='getService'),
    url(r'^service/modify/$', views.modifyService, name='modifyService'),
]
