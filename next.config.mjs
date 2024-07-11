/** @type {import('next').NextConfig} */
const nextConfig = {
    images: {
        domains: ['skillicons.dev'],
    },
    experimental: {
        serverComponentsExternalPackages: ['remark-prism']
      },
};

export default nextConfig;
