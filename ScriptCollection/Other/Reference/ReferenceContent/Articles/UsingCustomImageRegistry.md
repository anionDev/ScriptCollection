# Using custom image-registry

When you use third-party OCI-images (for example a base-image for your custom image or a database-image for integration-tests) then you need to take it from a registry.
By default, the [docker-hub](https://hub.docker.com/) will be used as registry if you do not specify any other registry.
The disadvantage of the docker-hub is the low rate-limit.
So it is recommended to host your own registry where you cache these images and then you can pull the images from your own registry without rate-limits.

ScriptCollections supports this.

How does it work?

On your development-machine and in your build-server-environment you have to create the file `~/.scriptcollection/GlobalCache/ImageCache.csv`.

In this file you can specify where the images should be taken from.

Example:

```csv
Image;UpstreamImage
myownregistry1.example.com/debian;docker.io/library/debian
myownregistry1.example.com/nginx;docker.io/library/nginx
myownregistry2.example.com/dotnetbase;mcr.microsoft.com/dotnet/aspnet
```

Translated to human language, this file means the following:

- When the image `debian` is required, then take it from `myownregistry1.example.com/debian` and use `docker.io/library/debian` as fallback.
- When the image `nginx` is required, then take it from `myownregistry1.example.com/nginx` and use `docker.io/library/nginx` as fallback.
- When the image `dotnetbase` is required, then take it from `myownregistry2.example.com/dotnetbase` and use `mcr.microsoft.com/dotnet/aspnet` as fallback.

The purpose of the fallback is that when you just did `git clone <myproject>` and want to use it, then it should just work.
ScriptCollection does not want to add mandatory requirements to the local development-environment apart from the existence of certain cli-tools.
And usually for the first run, it works even with the docker-hub as fallback-registry.
But since it is not recommended to use a fallback-registry, a warning will be displayed when the fallback-registry will be used.
