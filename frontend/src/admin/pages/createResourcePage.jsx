import ResourceCrudPage from "../components/ResourceCrudPage.jsx";

export function createResourcePage(resourceKey) {
  function ResourcePage() {
    return <ResourceCrudPage resourceKey={resourceKey} />;
  }

  ResourcePage.displayName = `${resourceKey}Page`;
  return ResourcePage;
}
